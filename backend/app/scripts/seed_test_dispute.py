import asyncio
from datetime import datetime, timedelta
from app.db.celery_session import get_celery_session
from app.models import Dispute, DisputeStatus, DisputeReason
from sqlalchemy import select

async def seed_test_dispute():
    async with get_celery_session() as db:
        # Select an existing transaction
        result = await db.execute(select(Dispute).limit(1))
        existing_dispute = result.scalars().first()

        if existing_dispute:
            print(f"Existing dispute found with ID: {existing_dispute.id}")
            return

        # If no dispute exists, select a transaction to base the dispute on
        result = await db.execute("SELECT id, merchant_id FROM transactions LIMIT 1")
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
            raised_at=datetime.utcnow() - timedelta(days=8),
            is_sla_breached=False,
            description="SLA checker test dispute"
        )
        db.add(dispute)
        await db.commit()
        print(f"Created test dispute with ID: {dispute.id}")

if __name__ == "__main__":
    asyncio.run(seed_test_dispute())