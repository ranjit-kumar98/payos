from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api.auth import get_current_user
from app.db.session import get_db
from app.services.fraud.query_service import FraudQueryService
from app.repositories.fraud_repository import FraudRepository
from app.schemas.fraud import HighRiskTransactionListResponse, HighRiskTransaction
from app.models import Merchant
from sqlalchemy import select

router = APIRouter(prefix="/fraud", tags=["fraud"], dependencies=[Depends(get_current_user)])

@router.get("/high-risk", response_model=HighRiskTransactionListResponse)
async def get_high_risk_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Find merchant for current user
    result = await db.execute(
        select(Merchant).where(Merchant.owner_id == current_user.id)
    )
    merchant = result.scalars().first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    repository = FraudRepository(db)
    service = FraudQueryService(repository)
    transactions = await service.get_high_risk_transactions(merchant.id, page, size)

    # For total count, a separate query or count can be implemented if needed.
    # For now, return only the current page items without total count.

    items = [
        HighRiskTransaction(
            transaction_id=str(t.id),
            merchant_id=str(t.merchant_id),
            amount=float(t.amount),
            currency=t.currency,
            payment_method=t.payment_method.value,
            status=t.status.value,
            risk_score=t.risk_score,
            risk_tier=t.risk_tier.value,
            triggered_rules=t.triggered_rules,
            created_at=t.created_at
        )
        for t in transactions
    ]

    return HighRiskTransactionListResponse(
        total=len(items),
        page=page,
        size=size,
        items=items
    )