from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, constr
from typing import Optional
from app.services.payment_routing_service import PaymentRoutingService
from app.api.auth import get_current_user
from app.models import PaymentMethod, TransactionStatus
from app.db.session import get_db
from sqlalchemy.orm import Session
import os
import razorpay
import uuid
from datetime import datetime

router = APIRouter(prefix="/payments", tags=["payments"])

class PaymentInitiationRequest(BaseModel):
    merchant_id: uuid.UUID
    amount: float = Field(..., gt=0)
    currency: constr(min_length=3, max_length=3) = Field(default="INR")
    payment_method: PaymentMethod

class PaymentInitiationResponse(BaseModel):
    razorpay_order_id: str
    amount: float
    currency: str
    selected_gateway: str
    estimated_gateway_fee: Optional[float]
    razorpay_key_id: Optional[str]

@router.post("/create-order", response_model=PaymentInitiationResponse)
async def create_order(
    request: PaymentInitiationRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Validate merchant_id matches user's merchant id
    if not user.merchant or str(user.merchant.id) != str(request.merchant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid merchant ID")
    routing_service = PaymentRoutingService(db)
    route = routing_service.route_payment(request.payment_method)
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active payment routes found")

    selected_gateway = route["selected_gateway"]
    backup_gateway = route["backup_gateway"]

    # For simplest fee calculation assume 2% fee
    estimated_fee = 0.02 * request.amount

    # Process Razorpay order creation if selected gateway is Razorpay
    if selected_gateway.lower() == "razorpay":
        key_id = os.getenv("RAZORPAY_KEY_ID")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        if not key_id or not key_secret:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Razorpay credentials not configured")
        client = razorpay.Client(auth=(key_id, key_secret))
        # Create order in test mode
        try:
            order_data = {
                "amount": int(request.amount * 100),  # amount in paise
                "currency": request.currency,
                "receipt": str(uuid.uuid4()),
                "payment_capture": 1,
                "notes": {"merchant_id": str(request.merchant_id)},
            }
            razorpay_order = client.order.create(data=order_data)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Razorpay order creation failed: {e}")

        razorpay_order_id = razorpay_order.get("id")

        # Save a PENDING transaction to DB
        from backend.app.models import Transaction
        transaction = Transaction(
            merchant_id=request.merchant_id,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            razorpay_order_id=razorpay_order_id,
            gateway_used=selected_gateway,
            gateway_fee=estimated_fee,
            status=TransactionStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return PaymentInitiationResponse(
            razorpay_order_id=razorpay_order_id,
            amount=request.amount,
            currency=request.currency,
            selected_gateway=selected_gateway,
            estimated_gateway_fee=estimated_fee,
            razorpay_key_id=key_id,
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Gateway {selected_gateway} not supported for order creation")