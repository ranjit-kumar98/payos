from typing import List
from datetime import datetime, timedelta
from app.repositories.fraud_repository import FraudRepository
from app.models import Transaction


class FraudQueryService:
    def __init__(self, repository: FraudRepository):
        self.repository = repository

    async def get_high_risk_transactions(
        self,
        merchant_id: str,
        page: int = 1,
        size: int = 20
    ) -> List[Transaction]:
        since = datetime.utcnow() - timedelta(hours=48)
        return await self.repository.get_high_risk_transactions(merchant_id, since, page, size)