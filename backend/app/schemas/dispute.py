from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel

from app.models import DisputeReason, DisputeStatus


class DisputeBase(BaseModel):
    transaction_id: UUID
    reason: DisputeReason
    description: Optional[str] = None


class DisputeCreate(DisputeBase):
    pass


class Dispute(BaseModel):
    id: UUID
    transaction_id: UUID
    merchant_id: UUID
    reason: DisputeReason
    description: Optional[str]
    status: DisputeStatus
    resolution_notes: Optional[str]
    raised_at: datetime
    resolved_at: Optional[datetime]
    is_sla_breached: bool
    sla_deadline: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class DisputeList(BaseModel):
    disputes: List[Dispute]
    total: int
