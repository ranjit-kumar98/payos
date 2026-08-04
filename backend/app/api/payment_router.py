from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.services.payment_routing_service import PaymentRoutingService
from app.api.auth import get_current_user
from app.db.session import get_db


router = APIRouter(prefix="/payments", tags=["payments"])

class PaymentRouteRequest(BaseModel):
    amount: float
    currency: str
    payment_method: str

class PaymentRouteResponse(BaseModel):
    selected_gateway: str
    backup_gateway: Optional[str]
    estimated_fee: float
    selection_reason: str

@router.post("/route", response_model=PaymentRouteResponse)
async def route_payment(
    request: PaymentRouteRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    routing_service = PaymentRoutingService(db)
    try:
        result = await routing_service.route_payment(
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result

from app.models import (
    Transaction,
    Merchant,
    PaymentMethod,
    TransactionStatus
)
# Removed import of User from app.schemas.auth due to ImportError
# User type will be replaced with current_user type from get_current_user dependency
from app.core.config import settings
from razorpay import Client
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
import uuid

@router.post("/create-order")
async def create_order(
    request: PaymentRouteRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Find merchant owned by current user
    try:
        result = await db.execute(select(Merchant).where(Merchant.owner_id == current_user.id))
        merchant = result.scalars().one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Merchant not found for current user")

    # Use PaymentRoutingService to get routing info
    routing_service = PaymentRoutingService(db)
    try:
        routing_result = await routing_service.route_payment(
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Initialize Razorpay client
    client = Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order using official SDK syntax
    order_data = {
        "amount": int(request.amount * 100),  # amount in paise
        "currency": request.currency,
        "receipt": f"receipt_{uuid.uuid4().hex[:12]}",
        "payment_capture": 1
    }
    razorpay_order = client.order.create(data=order_data)

    # Save transaction with merchant_id and PaymentMethod enum
    # transaction = Transaction(
    #     merchant_id=merchant.id,
    #     amount=request.amount,
    #     currency=request.currency,
    #     payment_method=PaymentMethod(request.payment_method),
    #     status="PENDING",
    #     razorpay_order_id=razorpay_order["id"]
    # )
    transaction = Transaction(
    merchant_id=merchant.id,
    razorpay_order_id=razorpay_order["id"],

    amount=request.amount,
    currency=request.currency,

    payment_method=PaymentMethod(request.payment_method),
    status=TransactionStatus.PENDING,

    gateway_used=routing_result["selected_gateway"],
    gateway_fee=routing_result["estimated_fee"],

    customer_email=current_user.email,
)
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    # Invalidate analytics cache for merchant
    from app.services.analytics_cache_service import invalidate_analytics_cache
    await invalidate_analytics_cache(merchant.id)
    print(f"Analytics cache invalidated for merchant: {merchant.id}")

    # Publish Kafka event payment.processed using KafkaProducerService
    from app.services.kafka.producer import KafkaProducerService

    await KafkaProducerService().publish(
        topic="payment.processed",
        event_type="payment.processed",
        payload={
            "transaction_id": str(transaction.id),
            "order_id": razorpay_order["id"],
            "merchant_id": str(merchant.id),
            "amount": float(request.amount),
            "currency": request.currency,
            "payment_method": request.payment_method,
            "status": transaction.status.value,
            "gateway_used": transaction.gateway_used,
            "gateway_fee": float(transaction.gateway_fee),
            "customer_email": current_user.email,
        },
        correlation_id=str(transaction.id),
    )

    return {
        "order_id": razorpay_order["id"],
        "key_id": settings.RAZORPAY_KEY_ID
    }
