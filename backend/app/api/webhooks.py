from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
from datetime import datetime, timedelta
from app.models import Transaction, TransactionStatus, Merchant
from app.core.config import settings
from razorpay.utility.utility import Utility
from app.services.kafka.producer import KafkaProducerService
from app.services.fraud.scoring_service import FraudScoringService
from app.db.session import get_db

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

print("=" * 80)
print("WEBHOOK FILE VERSION 2026-07-21")
print("=" * 80)

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    # Raw body exactly as Razorpay sent it
    body = await request.body()

    utility = Utility()

    try:
        utility.verify_webhook_signature(
            body.decode(),
            x_razorpay_signature,
            settings.RAZORPAY_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )

    # print("Webhook signature verified successfully")
    logger = logging.getLogger(__name__)

    payload = await request.json()

    try:
        order_id = payload["payload"]["payment"]["entity"]["order_id"]
    except (KeyError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid payload structure")

    try:
        result = await db.execute(select(Transaction).where(Transaction.razorpay_order_id == order_id))
        transaction = result.scalars().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Transaction not found")

    event = payload.get("event")

    if event == "payment.failed":
        transaction.status = TransactionStatus.FAILED
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        decline_reason = payment.get("error_description")
        if decline_reason:
            transaction.decline_reason = decline_reason

        payment_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id")
        if payment_id:
            transaction.razorpay_payment_id = payment_id


        transaction.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(transaction)

        logger.info("Publishing payment.failed Kafka event")
        try:
            await KafkaProducerService().publish(
                topic="payment.failed",
                event_type="payment.failed",
                payload={
                    "transaction_id": str(transaction.id),
                    "merchant_id": str(transaction.merchant_id),
                    "razorpay_order_id": transaction.razorpay_order_id,
                    "razorpay_payment_id": transaction.razorpay_payment_id,
                    "amount": float(transaction.amount),
                    "currency": transaction.currency,
                    "payment_method": transaction.payment_method.value,
                    "status": transaction.status.value,
                    "risk_score": float(transaction.risk_score) if transaction.risk_score is not None else None,
                    "risk_tier": transaction.risk_tier.value if transaction.risk_tier else None,
                    "decline_reason": transaction.decline_reason,
                },
                correlation_id=str(transaction.id),
            )
            logger.info("Kafka payment.failed event published")
        except Exception as e:
            logger.error(f"Failed to publish Kafka payment.failed event: {e}")

        return {
            "message": "Transaction updated",
            "transaction_id": transaction.id,
            "status": transaction.status.value if hasattr(transaction.status, "value") else str(transaction.status)
        }

    if event == "payment.captured":
        payment_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id")
        if payment_id:
            # Idempotency check: if already processed, return early
            if transaction.status == TransactionStatus.SUCCESS and transaction.razorpay_payment_id == payment_id:
                return {
                    "message": "Webhook already processed"
                }
            transaction.razorpay_payment_id = payment_id
        transaction.status = TransactionStatus.SUCCESS

        
        transaction_timestamp = datetime.utcnow()
        # Load merchant info
        result = await db.execute(select(Merchant).where(Merchant.id == transaction.merchant_id))
        merchant = result.scalars().first()
        merchant_created_at = (
            merchant.created_at if merchant else transaction_timestamp - timedelta(days=365)
        )
        merchant_risk_tier = getattr(merchant, "risk_tier", "LOW") if merchant else "LOW"

        is_weekend = int(transaction_timestamp.weekday() >= 5)

        logger.info("Starting fraud assessment")
        scoring_service = FraudScoringService()
        fraud_assessment = scoring_service.assess(
            amount=transaction.amount,
            currency=transaction.currency,
            payment_method=transaction.payment_method.value,
            transaction_timestamp=transaction_timestamp,
            merchant_created_at=merchant_created_at,
            merchant_risk_tier=merchant_risk_tier,
            is_weekend=is_weekend
        )
        logger.info(f"Fraud assessment completed: final_score={fraud_assessment.final_score}, risk_tier={fraud_assessment.risk_tier}")

        # Update transaction with fraud fields
        transaction.risk_score = fraud_assessment.final_score
        transaction.risk_tier = fraud_assessment.risk_tier
        transaction.triggered_rules = fraud_assessment.triggered_rules

        # If risk tier is HIGH, block transaction
        if fraud_assessment.risk_tier == "HIGH":
            transaction.status = TransactionStatus.BLOCKED
            logger.warning(f"Transaction {transaction.id} blocked due to high fraud risk")

        transaction.updated_at = transaction_timestamp

        await db.commit()
        await db.refresh(transaction)
        logger.info(f"Transaction {transaction.id} updated with fraud assessment")

        # Publish fraud.detected event if risk tier is MEDIUM or HIGH
        if fraud_assessment.risk_tier in ("MEDIUM", "HIGH"):
            kafka_payload = {
                "transaction_id": str(transaction.id),
                "merchant_id": str(transaction.merchant_id),
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "payment_method": transaction.payment_method.value,
                "risk_score": fraud_assessment.final_score,
                "risk_tier": (
                    fraud_assessment.risk_tier.value
                    if hasattr(fraud_assessment.risk_tier, "value")
                    else fraud_assessment.risk_tier
),
                "triggered_rules": fraud_assessment.triggered_rules,
                "status": transaction.status.value if hasattr(transaction.status, "value") else str(transaction.status)
            }
            logger.info("Publishing fraud.detected Kafka event")
            try:
                await KafkaProducerService().publish(
                    topic="fraud.detected",
                    event_type="fraud.detected",
                    payload=kafka_payload,
                    correlation_id=str(transaction.id)
                )
                logger.info("Kafka fraud.detected event published")
            except Exception as e:
                logger.error(f"Failed to publish Kafka fraud.detected event: {e}")

        # Publish payment.success or payment.failed events after transaction update
        if transaction.status == TransactionStatus.SUCCESS:
            logger.info(
                f"Publishing payment.success | transaction_id={transaction.id} | correlation_id={transaction.id}"
            )
            event_type = "payment.success"
            topic = "payment.success"
        elif transaction.status == TransactionStatus.FAILED:
            event_type = "payment.failed"
            topic = "payment.failed"
        else:
            event_type = None
            topic = None

        if event_type and topic:
            kafka_payload = {
                "transaction_id": str(transaction.id),
                "merchant_id": str(transaction.merchant_id),
                "razorpay_order_id": transaction.razorpay_order_id,
                "razorpay_payment_id": transaction.razorpay_payment_id,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "payment_method": transaction.payment_method.value,
                "status": transaction.status.value if hasattr(transaction.status, "value") else str(transaction.status),
                "risk_score": float(transaction.risk_score) if transaction.risk_score is not None else None,
                "risk_tier": transaction.risk_tier.value if transaction.risk_tier else None,
            }
            try:
                await KafkaProducerService().publish(
                    topic=topic,
                    event_type=event_type,
                    payload=kafka_payload,
                    correlation_id=str(transaction.id)
                )
                print("PUBLISHED payment.success")
                logger.info(f"Kafka {event_type} event published")
            except Exception as e:
                logger.error(f"Failed to publish Kafka {event_type} event: {e}")

        return {
            "message": "Transaction updated",
            "transaction_id": transaction.id,
            "status": transaction.status.value if hasattr(transaction.status, "value") else str(transaction.status)
        }
