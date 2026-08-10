import asyncio
from datetime import datetime, timedelta
from app.db.celery_session import get_celery_session
from app.models import Dispute, DisputeStatus, DisputeReason
from sqlalchemy import select

async def insert_test_dispute():
    async with get_celery_session() as db:
        # Select an existing transaction
        from sqlalchemy import text
        result = await db.execute(text("SELECT id, merchant_id FROM transactions LIMIT 1"))
        row = result.first()
        if not row:
            print("No transactions found in the database to create a dispute.")
            return

        transaction_id, merchant_id = row

        dispute = Dispute(
            transaction_id=transaction_id,
            merchant_id=merchant_id,
            status=DisputeStatus.RAISED,
            reason=DisputeReason.FRAUD,
            description="SLA checker test dispute",
            raised_at=datetime.utcnow() - timedelta(days=8),
            is_sla_breached=False
        )
        db.add(dispute)
        await db.commit()
        print(f"Created test dispute with ID: {dispute.id}")
        print(f"raised_at: {dispute.raised_at}, status: {dispute.status}, is_sla_breached: {dispute.is_sla_breached}")

if __name__ == "__main__":
    asyncio.run(insert_test_dispute())