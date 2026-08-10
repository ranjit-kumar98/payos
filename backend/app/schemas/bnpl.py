from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class BnplRepaymentScheduleResponse(BaseModel):
    month: int
    emi: Decimal
    interest: Decimal
    principal: Decimal
    remaining_balance: Decimal
    model_config = {"from_attributes": True}


class BnplLoanCreateRequest(BaseModel):
    principal: Decimal = Field(
        ...,
        description="Principal amount for the BNPL loan",
    )
    tenure: int = Field(
        ...,
        description="Loan tenure in months",
    )
    transaction_id: str | None = Field(
        None,
        description="Associated transaction ID, if any",
    )


class BnplLoanResponse(BaseModel):
    id: str
    principal: Decimal
    tenure_months: int
    annual_interest_rate: Decimal
    monthly_emi: Decimal
    total_interest: Decimal
    total_repayment: Decimal
    status: str
    repayment_schedule: List[BnplRepaymentScheduleResponse]
    created_at: datetime
    model_config = {"from_attributes": True}