from datetime import date, datetime
from decimal import Decimal
from typing import List, Any
from uuid import UUID
from pydantic import BaseModel, Field


class FraudReportResponse(BaseModel):
    id: UUID = Field(..., description="UUID of the fraud report")
    report_date: date = Field(..., description="Date of the report")
    total_transactions: int = Field(..., description="Total number of transactions")
    blocked_transactions: int = Field(..., description="Number of blocked transactions")
    blocked_amount: Decimal = Field(..., description="Total amount blocked")
    top_triggered_rules: List[Any] = Field(..., description="List of top triggered rules")
    created_at: datetime = Field(..., description="Timestamp when the report was created")

    class Config:
        orm_mode = True
