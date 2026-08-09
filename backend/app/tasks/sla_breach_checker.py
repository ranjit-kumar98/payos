import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.celery_app import celery_app
from app.models import Dispute, DisputeStatus
from app.db.celery_session import get_celery_session
from app.services.kafka.producer import KafkaProducerService

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.sla_breach_checker.check_sla_breaches_task")
def check_sla_breaches_task():
    logger.info("Starting SLA breach check task")
    asyncio.run(_check_sla_breaches())

async def _check_sla_breaches():
    async with get_celery_session() as db:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        try:
            # Query disputes with status RAISED or UNDER_REVIEW, older than 7 days, and not yet SLA breached
            stmt = select(Dispute).where(
                or_(
                    Dispute.status == DisputeStatus.RAISED,
                    Dispute.status == DisputeStatus.UNDER_REVIEW
                ),
                Dispute.raised_at < seven_days_ago,
                Dispute.is_sla_breached == False
            )
            result = await db.execute(stmt)
            disputes = result.scalars().all()

            if not disputes:
                logger.info("No disputes found for SLA breach update")
                return

            kafka_producer = KafkaProducerService()

            for dispute in disputes:
                dispute.is_sla_breached = True
                await db.flush()  # flush update before publishing event

                event_payload = {
                    "dispute_id": str(dispute.id),
                    "transaction_id": str(dispute.transaction_id),
                    "merchant_id": str(dispute.merchant_id),
                    "status": dispute.status.value,
                    "raised_at": dispute.raised_at.isoformat() if dispute.raised_at else None,
                    "is_sla_breached": dispute.is_sla_breached,
                }

                await kafka_producer.publish(
                    topic="dispute.sla_breached",
                    event_type="dispute.sla_breached",
                    payload=event_payload,
                    correlation_id=str(dispute.id)
                )
                logger.info(f"Published SLA breach event for dispute {dispute.id}")

            await db.commit()
            logger.info("SLA breach check task completed successfully")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error during SLA breach check task: {e}")
            raise
