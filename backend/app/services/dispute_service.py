from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Dispute,
    Transaction,
    Merchant,
    TransactionStatus,
    DisputeStatus,
    DisputeReason,
)
import json
import logging

from app.services.kafka.consumer import KafkaConsumerService
from app.services.kafka.producer import KafkaProducerService
from app.tasks.dispute_email import send_dispute_raised_email, send_dispute_resolution_email

logger = logging.getLogger(__name__)


class DisputeService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.kafka_producer = KafkaProducerService()

    async def mark_sla_breaches(self):
        """
        Find disputes with status RAISED or UNDER_REVIEW,
        ignore disputes already marked is_sla_breached=True,
        determine breach using dispute.sla_deadline,
        set is_sla_breached=True for overdue disputes,
        commit the changes,
        and return the disputes that were marked as breached.
        """
        from datetime import datetime
        from sqlalchemy import select
        from app.models import Dispute, DisputeStatus

        stmt = select(Dispute).where(
            Dispute.status.in_([DisputeStatus.RAISED, DisputeStatus.UNDER_REVIEW]),
            Dispute.is_sla_breached == False,
            Dispute.sla_deadline != None
        )
        result = await self.db_session.execute(stmt)
        disputes = result.scalars().all()

        breached_disputes = []
        now = datetime.utcnow()
        for dispute in disputes:
            if dispute.sla_deadline and now > dispute.sla_deadline:
                dispute.is_sla_breached = True
                breached_disputes.append(dispute)

        if breached_disputes:
            await self.db_session.commit()

        return breached_disputes
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

        merchant = await self.db_session.get(Merchant, transaction.merchant_id)
        if not merchant:
            raise ValueError("Merchant not found")

        merchant_email = merchant.email
        customer_email = transaction.customer_email

        

        # Publish Kafka event dispute.raised
        try:
            event_payload = {
                "dispute_id": str(dispute.id),
                "transaction_id": str(dispute.transaction_id),
                "merchant_id": str(dispute.merchant_id),
                "reason": dispute.reason.value,
                "status": dispute.status.value,
                "raised_at": dispute.raised_at.isoformat(),
                "sla_deadline": dispute.sla_deadline.isoformat(),
            }
            await self.kafka_producer.publish(
                topic="dispute.raised",
                event_type="dispute.raised",
                payload=event_payload,
            )
        except Exception as e:
            logger.error(f"Failed to publish dispute.raised event: {e}")

        # Queue Celery email task to notify merchant
        try:
            email_payload = {
                "merchant_email": merchant_email,
                "merchant_id": str(dispute.merchant_id),
                "dispute_id": str(dispute.id),
                "transaction_id": str(dispute.transaction_id),
                "reason": dispute.reason.value,
                "status": dispute.status.value,
                "raised_at": dispute.raised_at.isoformat(),
                "sla_deadline": dispute.sla_deadline.isoformat(),
            }
            send_dispute_raised_email.delay(email_payload)
        except Exception as e:
            logger.error(f"Failed to queue dispute raised email task: {e}")

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

    async def move_to_review(self, dispute_id: UUID) -> Dispute:
        dispute = await self.db_session.get(Dispute, dispute_id)
        if not dispute:
            raise ValueError("Dispute not found")
        if dispute.status != DisputeStatus.RAISED:
            raise RuntimeError("Only RAISED disputes can be moved to UNDER_REVIEW")
        dispute.status = DisputeStatus.UNDER_REVIEW
        dispute.updated_at = datetime.utcnow()
        self.db_session.add(dispute)
        await self.db_session.commit()
        await self.db_session.refresh(dispute)
        return dispute

    async def resolve_dispute(self, dispute_id: UUID, resolution_notes: str) -> Dispute:
        dispute = await self.db_session.get(Dispute, dispute_id)
        if not dispute:
            raise ValueError("Dispute not found")

        transaction = await self.db_session.get(Transaction, dispute.transaction_id)
        merchant = await self.db_session.get(Merchant, dispute.merchant_id)

        if not transaction:
            raise ValueError("Transaction not found")

        if not merchant:
            raise ValueError("Merchant not found")
        
        if dispute.status != DisputeStatus.UNDER_REVIEW:
            raise RuntimeError("Only UNDER_REVIEW disputes can be resolved")
        if not resolution_notes or resolution_notes.strip() == "":
            raise ValueError("resolution_notes is required and must not be empty")
        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution_notes = resolution_notes
        dispute.resolved_at = datetime.utcnow()
        dispute.updated_at = datetime.utcnow()
        self.db_session.add(dispute)
        await self.db_session.commit()
        await self.db_session.refresh(dispute)

        # Publish Kafka event dispute.resolved
        try:
            event_payload = {
                "dispute_id": str(dispute.id),
                "transaction_id": str(dispute.transaction_id),
                "merchant_id": str(dispute.merchant_id),
                "customer_email":transaction.customer_email,
                "status": dispute.status.value,
                "resolution_notes": dispute.resolution_notes,
                "resolved_at": dispute.resolved_at.isoformat(),
            }

            await self.kafka_producer.publish(
                topic="dispute.resolved",
                event_type="dispute.resolved",
                payload=event_payload,
            )

        except Exception as e:
            logger.error(f"Failed to publish dispute.resolved event: {e}")

        # Queue Celery email task to notify merchant and customer
        try:
            email_payload = {
                "merchant_email": merchant.email,
                "customer_email": transaction.customer_email,
                "merchant_id": str(dispute.merchant_id),
                "dispute_id": str(dispute.id),
                "transaction_id": str(dispute.transaction_id),
                "status": dispute.status.value,
                "resolution_notes": dispute.resolution_notes,
                "resolved_at": dispute.resolved_at.isoformat(),
            }

            send_dispute_resolution_email.delay(email_payload)

        except Exception as e:
            logger.error(f"Failed to queue dispute resolved email task: {e}")

        return dispute

    async def reject_dispute(self, dispute_id: UUID, resolution_notes: str) -> Dispute:
        dispute = await self.db_session.get(Dispute, dispute_id)
        if not dispute:
            raise ValueError("Dispute not found")
        if dispute.status != DisputeStatus.UNDER_REVIEW:
            raise RuntimeError("Only UNDER_REVIEW disputes can be rejected")
        if not resolution_notes or resolution_notes.strip() == "":
            raise ValueError("resolution_notes is required and must not be empty")
        dispute.status = DisputeStatus.REJECTED
        dispute.resolution_notes = resolution_notes
        dispute.resolved_at = datetime.utcnow()
        dispute.updated_at = datetime.utcnow()
        self.db_session.add(dispute)
        await self.db_session.commit()
        await self.db_session.refresh(dispute)

        transaction = await self.db_session.get(Transaction, dispute.transaction_id)
        merchant = await self.db_session.get(Merchant, dispute.merchant_id)

        if not transaction:
            raise ValueError("Transaction not found")

        if not merchant:
            raise ValueError("Merchant not found")

        # Publish Kafka event dispute.rejected
        try:
            event_payload = {
                "dispute_id": str(dispute.id),
                "transaction_id": str(dispute.transaction_id),
                "merchant_id": str(dispute.merchant_id),
                "customer_email": transaction.customer_email,
                "status": dispute.status.value,
                "resolution_notes": dispute.resolution_notes,
                "resolved_at": dispute.resolved_at.isoformat(),
            }
            await self.kafka_producer.publish(
                topic="dispute.rejected",
                event_type="dispute.rejected",
                payload=event_payload,
            )
        except Exception as e:
            logger.error(f"Failed to publish dispute.rejected event: {e}")

        # Queue Celery email task to notify merchant and customer
        try:
            email_payload = {
                "merchant_email":  merchant.email,
                "customer_email": transaction.customer_email,
                "merchant_id": str(dispute.merchant_id),
                "dispute_id": str(dispute.id),
                "transaction_id": str(dispute.transaction_id),
                "status": dispute.status.value,
                "resolution_notes": dispute.resolution_notes,
                "resolved_at": dispute.resolved_at.isoformat(),
            }
            send_dispute_resolution_email.delay(email_payload)
        except Exception as e:
            logger.error(f"Failed to queue dispute rejected email task: {e}")

        return dispute
