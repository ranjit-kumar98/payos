from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import Transaction, TransactionStatus
from app.core.config import settings
from razorpay.utility.utility import Utility

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

    print("Webhook signature verified successfully")

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

    return {
        "message": "Transaction updated",
        "transaction_id": transaction.id,
        "status": transaction.status
    }
