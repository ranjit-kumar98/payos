
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
import asyncio
from datetime import datetime, timedelta
from app.models import Merchant, Transaction, Dispute, TransactionStatus

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

from app.models import PaymentMethod, TransactionStatus
from sqlalchemy import case

async def get_payment_method_breakdown(db: AsyncSession, owner_id: int, days: int = 30):
    # Find merchant for current user
    result = await db.execute(select(Merchant).filter(Merchant.owner_id == owner_id))
    merchant = result.scalars().first()
    if not merchant:
        return None

    merchant_id = merchant.id

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    payment_methods = [PaymentMethod.UPI, PaymentMethod.CARD, PaymentMethod.WALLET, PaymentMethod.NETBANKING]

    # Query payment method breakdown
    query = (
        select(
            Transaction.payment_method.label("method"),
            func.count(Transaction.id).label("count"),
            func.coalesce(func.sum(case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)), 0).label("total_gmv"),
            (func.count(case((Transaction.status == TransactionStatus.SUCCESS, 1))) * 100.0 / func.count(Transaction.id)).label("success_rate")
        )
        .filter(
            Transaction.merchant_id == merchant_id,
            Transaction.created_at >= cutoff_date,
            Transaction.payment_method.in_(payment_methods)
        )
        .group_by(Transaction.payment_method)
    )

    result = await db.execute(query)
    rows = result.all()

    # Build dict for quick lookup
    data_by_method = {
    row.method.value if hasattr(row.method, "value") else row.method: {
        "method": row.method.value if hasattr(row.method, "value") else row.method,
        "count": row.count,
        "total_gmv": round(float(row.total_gmv), 2),
        "success_rate": round(float(row.success_rate) if row.success_rate is not None else 0.0, 2)
    }
    for row in rows
}

    # Ensure all payment methods are present
    breakdown = []
    for method in payment_methods:
        method_value = method.value if hasattr(method, 'value') else method
        if method_value in data_by_method:
            breakdown.append(data_by_method[method_value])
        else:
            breakdown.append({
                "method": method_value,
                "count": 0,
                "total_gmv": 0.0,
                "success_rate": 0.0
            })

    return breakdown

async def get_decline_reasons(db: AsyncSession, owner_id: int, days: int = 30):
    # Find merchant for current user
    result = await db.execute(select(Merchant).filter(Merchant.owner_id == owner_id))
    merchant = result.scalars().first()
    if not merchant:
        return None

    merchant_id = merchant.id

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query total failed transactions count
    total_failed_stmt = select(func.count(Transaction.id)).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.created_at >= cutoff_date,
        Transaction.status == TransactionStatus.FAILED
    )
    total_failed_result = await db.execute(total_failed_stmt)
    total_failed = total_failed_result.scalar() or 0

    if total_failed == 0:
        return []

    # Query top 5 decline reasons
    decline_query = (
        select(
            Transaction.decline_reason.label("reason"),
            func.count(Transaction.id).label("count")
        )
        .filter(
            Transaction.merchant_id == merchant_id,
            Transaction.created_at >= cutoff_date,
            Transaction.status == TransactionStatus.FAILED,
            Transaction.decline_reason.isnot(None)
        )
        .group_by(Transaction.decline_reason)
        .order_by(func.count(Transaction.id).desc())
        .limit(5)
    )

    decline_result = await db.execute(decline_query)
    rows = decline_result.all()

    # Build response list with percentage
    reasons = []
    for row in rows:
        percentage = (row.count / total_failed) * 100 if total_failed > 0 else 0.0
        reasons.append({
            "reason": row.reason,
            "count": row.count,
            "percentage": round(percentage, 2)
        })

    return reasons

async def get_fraud_heatmap(db: AsyncSession, owner_id: int, days: int = 30):
    from datetime import datetime, timedelta
    from sqlalchemy import select, func
    from app.models import Merchant, Transaction, RiskTier

    # Find merchant for current user
    result = await db.execute(select(Merchant).filter(Merchant.owner_id == owner_id))
    merchant = result.scalars().first()
    if not merchant:
        return None
    merchant_id = merchant.id

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Query counts grouped by hour and risk tier
    query = (
        select(
            func.extract('hour', Transaction.created_at).label('hour'),
            Transaction.risk_tier,
            func.count(Transaction.id).label('count')
        )
        .filter(
            Transaction.merchant_id == merchant_id,
            Transaction.created_at >= cutoff
        )
        .group_by('hour', Transaction.risk_tier)
        .order_by('hour')
    )
    result = await db.execute(query)
    rows = result.all()

    # Initialize 24 buckets with zero counts
    heatmap = []
    for hour in range(24):
        heatmap.append({
            'hour': hour,
            'low_risk_count': 0,
            'medium_risk_count': 0,
            'high_risk_count': 0
        })

    # Fill counts from query results
    for row in rows:
        hour = int(row.hour)
        tier = row.risk_tier
        count = row.count
        if tier == RiskTier.LOW:
            heatmap[hour]['low_risk_count'] = count
        elif tier == RiskTier.MEDIUM:
            heatmap[hour]['medium_risk_count'] = count
        elif tier == RiskTier.HIGH:
            heatmap[hour]['high_risk_count'] = count

    return heatmap

async def get_top_merchants(db: AsyncSession, owner_id: int, days: int = 30):
    from datetime import datetime, timedelta
    from sqlalchemy import select, func, case
    from app.models import Merchant, Transaction, Dispute

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Subquery for total transactions and successful transactions per merchant
    total_tx_subq = (
        select(
            Transaction.merchant_id,
            func.count(Transaction.id).label('total_tx'),
            func.count(case((Transaction.status == TransactionStatus.SUCCESS, 1))).label('success_tx'),
            func.coalesce(func.sum(case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)), 0).label('total_gmv')
        )
        .filter(Transaction.created_at >= cutoff)
        .group_by(Transaction.merchant_id)
        .subquery()
    )

    # Subquery for disputes count per merchant
    dispute_subq = (
        select(
            Dispute.merchant_id,
            func.count(Dispute.id).label('dispute_count')
        )
        .filter(Dispute.raised_at >= cutoff)
        .group_by(Dispute.merchant_id)
        .subquery()
    )

    # Join merchants with subqueries
    query = (
        select(
            Merchant.name.label('merchant_name'),
            Merchant.business_type,
            total_tx_subq.c.total_gmv,
            total_tx_subq.c.total_tx,
            (total_tx_subq.c.success_tx * 100.0 / total_tx_subq.c.total_tx).label('success_rate'),
            (func.coalesce(dispute_subq.c.dispute_count, 0) * 100.0 / total_tx_subq.c.total_tx).label('dispute_rate')
        )
        .join(total_tx_subq, Merchant.id == total_tx_subq.c.merchant_id)
        .outerjoin(dispute_subq, Merchant.id == dispute_subq.c.merchant_id)
        .order_by(total_tx_subq.c.total_gmv.desc())
        .limit(10)
    )

    result = await db.execute(query)
    rows = result.all()

    # Format results
    top_merchants = []
    for row in rows:
        top_merchants.append({
            'merchant_name': row.merchant_name,
            'business_type': row.business_type.value if row.business_type else None,
            'gmv': float(row.total_gmv),
            'transaction_count': row.total_tx,
            'success_rate': round(float(row.success_rate), 2) if row.success_rate is not None else 0.0,
            'dispute_rate': round(float(row.dispute_rate), 2) if row.dispute_rate is not None else 0.0
        })

    return top_merchants