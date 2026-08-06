import logging
from datetime import datetime, timezone
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.models import FraudReport, Transaction

logger = logging.getLogger(__name__)

async def generate_daily_fraud_report():
    logger.info("Generating fraud report...")
    async with async_session() as db:
        async with db.begin():
            try:
                # Calculate total transactions
                total_transactions_result = await db.execute(
                    select(func.count(Transaction.id))
                )
                total_transactions = total_transactions_result.scalar() or 0

                # Calculate blocked transactions
                blocked_transactions_result = await db.execute(
                    select(func.count(Transaction.id)).where(Transaction.status == "BLOCKED")
                )
                blocked_transactions = blocked_transactions_result.scalar() or 0

                # Calculate blocked amount
                blocked_amount_result = await db.execute(
                    select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.status == "BLOCKED")
                )
                blocked_amount = blocked_amount_result.scalar() or 0

                # No FraudRuleTrigger data exists, so set empty list
                top_triggered_rules = []

                # Create FraudReport record
                report = FraudReport(
                    report_date=datetime.now(timezone.utc).date(),
                    total_transactions=total_transactions,
                    blocked_transactions=blocked_transactions,
                    blocked_amount=blocked_amount,
                    top_triggered_rules=top_triggered_rules
                )
                db.add(report)
                await db.flush()  # flush to get id if needed

                logger.info("Fraud report saved successfully")
                return report
            except Exception as e:
                await db.rollback()
                logger.error(f"Error generating fraud report: {e}")
                raise
