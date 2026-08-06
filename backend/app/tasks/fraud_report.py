import logging
import asyncio
from app.celery_app import celery_app
from app.services.fraud_report_service import generate_daily_fraud_report
from app.db.celery_session import get_celery_session

logger = logging.getLogger(__name__)

async def _generate_daily_fraud_report():
    async with get_celery_session() as db:
        await generate_daily_fraud_report()

@celery_app.task(name="app.tasks.fraud_report.generate_daily_fraud_report_task")
def generate_daily_fraud_report_task():
    logger.info("Starting daily fraud report generation")
    asyncio.run(_generate_daily_fraud_report())
    logger.info("Daily fraud report completed")