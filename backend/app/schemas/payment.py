from pydantic import BaseModel
import uuid
from app.models import PaymentMethod
from typing import Optional

class PaymentInitiationRequest(BaseModel):
    merchant_id: uuid.UUID
    amount: float
    currency: str
    payment_method: PaymentMethod

class PaymentInitiationResponse(BaseModel):
    razorpay_order_id: str
    amount: float
    currency: str
    selected_gateway: str
    estimated_gateway_fee: float
    razorpay_key_id: Optional[str]