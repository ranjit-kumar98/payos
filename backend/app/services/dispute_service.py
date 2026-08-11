from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Dispute, Transaction, TransactionStatus, DisputeStatus, DisputeReason


class DisputeService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def raise_dispute(self, transaction_id: UUID, reason: DisputeReason, description: Optional[str] = None) -> Dispute:
        # Validate transaction existence
        transaction = await self.db_session.get(Transaction, transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")

        # Validate transaction status
        if transaction.status != TransactionStatus.SUCCESS:
            raise ValueError("Transaction status must be SUCCESS to raise dispute")

        # Check if dispute already exists for this transaction
        existing_dispute = await self.db_session.execute(
            select(Dispute).where(Dispute.transaction_id == transaction_id)
        )
        if existing_dispute.scalars().first():
            raise RuntimeError("Dispute already exists for this transaction")

        now = datetime.utcnow()
        sla_deadline = now + timedelta(days=7)

        dispute = Dispute(
            transaction_id=transaction_id,
            merchant_id=transaction.merchant_id,
            reason=reason,
            description=description,
            status=DisputeStatus.RAISED,
            raised_at=now,
            sla_deadline=sla_deadline,
            is_sla_breached=False,
        )
        self.db_session.add(dispute)
        await self.db_session.commit()
        await self.db_session.refresh(dispute)
        return dispute

    async def list_disputes(
        self,
        status: Optional[DisputeStatus] = None,
        merchant_id: Optional[UUID] = None,
    ) -> List[Dispute]:
        query = select(Dispute)

        if status:
            query = query.where(Dispute.status == status)
        if merchant_id:
            query = query.where(Dispute.merchant_id == merchant_id)

        result = await self.db_session.execute(query)
        disputes = result.scalars().all()

        # Mark overdue unresolved disputes as SLA breached
        now = datetime.utcnow()
        sla_breached_ids = []
        for dispute in disputes:
            if (
                dispute.status in (DisputeStatus.RAISED, DisputeStatus.UNDER_REVIEW)
                and now > dispute.sla_deadline
                and not dispute.is_sla_breached
            ):
                dispute.is_sla_breached = True
                sla_breached_ids.append(dispute.id)

        if sla_breached_ids:
            await self.db_session.commit()

        return disputes

    async def get_dispute(self, dispute_id: UUID) -> Optional[Dispute]:
        dispute = await self.db_session.get(Dispute, dispute_id)
        return dispute