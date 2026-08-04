from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.db.session import get_db
from app.schemas.analytics import AnalyticsOverviewResponse
from app.services.analytics_service import get_merchant_analytics
from app.services.analytics_cache_service import (
    get_analytics_cache,
    set_analytics_cache,
)
import json
import logging

router = APIRouter()

from fastapi import Depends
from app.services.rate_limit_dependency import rate_limit_dependency

from fastapi import Depends
from app.services.rate_limit_dependency import rate_limit_dependency

@router.get("/overview", response_model=AnalyticsOverviewResponse, dependencies=[Depends(rate_limit_dependency)])
async def analytics_overview(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models import Merchant
    from sqlalchemy import select

    result = await db.execute(select(Merchant).filter(Merchant.owner_id == current_user.id))
    merchant = result.scalars().first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for current user"
        )
    merchant_id = merchant.id

    cached = await get_analytics_cache(merchant_id)
    if cached:
        print("========== CACHE HIT ==========")
        return cached

    print("========== CACHE MISS ==========")
    analytics = await get_merchant_analytics(db, current_user.id)
    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for current user"
        )
    await set_analytics_cache(merchant_id, analytics, expires_seconds=300)
    logging.info("Analytics Cache SET (TTL=300)")

    return analytics
