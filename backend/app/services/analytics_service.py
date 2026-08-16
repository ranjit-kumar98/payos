
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from app.models import Merchant, Transaction
import asyncio
from datetime import datetime, timedelta

async def get_merchant_analytics(db: AsyncSession, owner_id: int, days: int = 30):
    # Find merchant for current user
    result = await db.execute(select(Merchant).filter(Merchant.owner_id == owner_id))
    merchant = result.scalars().first()
    if not merchant:
        return None

    merchant_id = merchant.id

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Prepare queries with date filtering
    total_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.created_at >= cutoff_date
    )
    successful_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "SUCCESS",
        Transaction.created_at >= cutoff_date
    )
    failed_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "FAILED",
        Transaction.created_at >= cutoff_date
    )
    pending_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "PENDING",
        Transaction.created_at >= cutoff_date
    )
    blocked_transactions_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "BLOCKED",
        Transaction.created_at >= cutoff_date
    )
    total_successful_volume_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.status == "SUCCESS",
        Transaction.created_at >= cutoff_date
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

async def get_daily_gmv_trend(db: AsyncSession, owner_id: int, days: int = 30):
    # Find merchant for current user
    result = await db.execute(select(Merchant).filter(Merchant.owner_id == owner_id))
    merchant = result.scalars().first()
    if not merchant:
        return None

    merchant_id = merchant.id

    cutoff_date = datetime.utcnow().date() - timedelta(days=days - 1)

    # Query daily aggregated data grouped by date
    daily_query = (
        select(
            cast(Transaction.created_at, Date).label("date"),
            func.count(Transaction.id).label("transaction_count"),
            func.count(Transaction.id).filter(Transaction.status == "SUCCESS").label("success_count"),
            func.count(Transaction.id).filter(Transaction.status == "FAILED").label("failed_count"),
            func.count(Transaction.id).filter(Transaction.status == "BLOCKED").label("blocked_count"),
            func.coalesce(func.sum(Transaction.amount).filter(Transaction.status == "SUCCESS"), 0).label("total_gmv")
        )
        .filter(
            Transaction.merchant_id == merchant_id,
            Transaction.created_at >= cutoff_date
        )
        .group_by("date")
        .order_by("date")
    )

    result = await db.execute(daily_query)
    rows = result.all()

    # Build a dict keyed by date string for quick lookup
    data_by_date = {row.date.strftime("%Y-%m-%d"): {
        "date": row.date.strftime("%Y-%m-%d"),
        "transaction_count": row.transaction_count,
        "success_count": row.success_count,
        "failed_count": row.failed_count,
        "blocked_count": row.blocked_count,
        "total_gmv": round(float(row.total_gmv), 2)
    } for row in rows}

    # Fill in missing dates with zeros
    trend = []
    for i in range(days):
        day = (cutoff_date + timedelta(days=i)).strftime("%Y-%m-%d")
        if day in data_by_date:
            trend.append(data_by_date[day])
        else:
            trend.append({
                "date": day,
                "transaction_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "blocked_count": 0,
                "total_gmv": 0.0
            })

    return trend
