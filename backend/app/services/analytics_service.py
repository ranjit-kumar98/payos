from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Merchant, Transaction
import asyncio

async def get_merchant_analytics(db: AsyncSession, owner_id: int):
    # Find merchant for current user
    result = await db.execute(select(Merchant).filter(Merchant.owner_id == owner_id))
    merchant = result.scalars().first()
    if not merchant:
        return None

    merchant_id = merchant.id

    # Prepare queries
    total_transactions_stmt = select(func.count(Transaction.id)).filter(Transaction.merchant_id == merchant_id)
    successful_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "SUCCESS"
    )
    failed_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "FAILED"
    )
    pending_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "PENDING"
    )
    blocked_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "BLOCKED"
    )
    total_successful_volume_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "SUCCESS"
    )

    # Execute all queries concurrently
    results = await asyncio.gather(
        db.execute(total_transactions_stmt),
        db.execute(successful_transactions_stmt),
        db.execute(failed_transactions_stmt),
        db.execute(pending_transactions_stmt),
        db.execute(blocked_transactions_stmt),
        db.execute(total_successful_volume_stmt),
    )

    total_transactions = results[0].scalar() or 0
    successful_transactions = results[1].scalar() or 0
    failed_transactions = results[2].scalar() or 0
    pending_transactions = results[3].scalar() or 0
    blocked_transactions = results[4].scalar() or 0
    total_successful_volume = results[5].scalar() or 0.0

    success_rate = 0.0
    if total_transactions > 0:
        success_rate = round((successful_transactions / total_transactions) * 100, 2)

    return {
        "total_transactions": total_transactions,
        "successful_transactions": successful_transactions,
        "failed_transactions": failed_transactions,
        "pending_transactions": pending_transactions,
        "blocked_transactions": blocked_transactions,
        "total_successful_volume": float(total_successful_volume),
        "success_rate": success_rate
    }
