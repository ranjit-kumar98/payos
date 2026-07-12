from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models import Transaction
from app.models import RiskTier

class FraudRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_high_risk_transactions(
        self,
        merchant_id: str,
        since: datetime,
        page: int = 1,
        size: int = 20
    ) -> List[Transaction]:
        offset = (page - 1) * size
        query = (
            select(Transaction)
            .where(
                Transaction.risk_tier == RiskTier.HIGH,
                Transaction.created_at >= since,
                Transaction.merchant_id == merchant_id
            )
            .order_by(desc(Transaction.risk_score), desc(Transaction.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        return result.scalars().all()