from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models import PaymentMethod, TransactionStatus


class HighRiskTransaction(BaseModel):
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str
    payment_method: str
    status: str
    risk_score: float
    risk_tier: str
    triggered_rules: List[str]
    created_at: datetime

class HighRiskTransactionListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[HighRiskTransaction]