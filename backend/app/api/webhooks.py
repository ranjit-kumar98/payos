from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

from app.db.session import get_db
from app.models import Transaction, TransactionStatus
from app.core.config import settings
from razorpay.utility.utility import Utility
from app.services.kafka_producer import KafkaProducer
from app.models import TransactionStatus
from datetime import datetime

import logging

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


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

    if event == "payment.captured":
        transaction.status = TransactionStatus.SUCCESS
    elif event == "payment.failed":
        transaction.status = TransactionStatus.FAILED
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        decline_reason = payment.get("error_description")
        if decline_reason:
            transaction.decline_reason = decline_reason

    payment_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id")
    if payment_id:
        transaction.razorpay_payment_id = payment_id

    from datetime import datetime
    transaction.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(transaction)

    # Publish Kafka event after successful commit
    event_type = None
    topic = None
    payload = {
        "transaction_id": str(transaction.id),
        "merchant_id": str(transaction.merchant_id),
        "amount": float(transaction.amount),
        "status": transaction.status.value,
        "payment_method": transaction.payment_method.value,
        "razorpay_payment_id": transaction.razorpay_payment_id,
    }

    if event == "payment.captured":
        event_type = "payment.captured"
        topic = "payment.processed"
    elif event == "payment.failed":
        event_type = "payment.failed"
        topic = "payment.failed"

    if event_type and topic:
        kafka_event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "correlation_id": str(uuid.uuid4()),
            "payload": payload,
        }

        logger.info(
            f"Publishing payment event to Kafka topic '{topic}' "
            f"(transaction_id={transaction.id})"
        )

        try:
            await KafkaProducer.publish(topic, kafka_event)

            logger.info(
                f"Kafka event published successfully to '{topic}' "
                f"(transaction_id={transaction.id})"
            )

        except Exception:
            logger.exception(
                f"Failed to publish Kafka event to topic '{topic}' "
                f"(transaction_id={transaction.id})"
            )