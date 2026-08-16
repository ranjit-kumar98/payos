from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.services.rate_limit_dependency import rate_limit_dependency
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.db.session import get_db
from app.schemas.analytics import AnalyticsOverviewResponse, DailyGMVTrendResponse, PaymentMethodBreakdownResponse, DeclineReasonsResponse
from app.services.analytics_service import get_merchant_analytics, get_daily_gmv_trend, get_payment_method_breakdown, get_decline_reasons
from app.services.analytics_cache_service import (
    get_analytics_cache,
    set_analytics_cache,
)
import json
import logging

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverviewResponse, dependencies=[Depends(rate_limit_dependency)])
async def analytics_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics data"),
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

    # For days=30, check existing Celery precomputed cache key first
    if days == 30:
        celery_cache_key = f"analytics:overview:{merchant_id}"
        cached = await get_analytics_cache(celery_cache_key)
        if cached:
            print("========== CELERY CACHE HIT ==========")
            return cached

    # For other days or cache miss, use new day-specific cache key
    cache_key = f"analytics:overview:merchant:{merchant_id}:days:{days}"
    cached = await get_analytics_cache(cache_key)
    if cached:
        print("========== CACHE HIT ==========")
        return cached

    print("========== CACHE MISS ==========")
    analytics = await get_merchant_analytics(db, current_user.id, days=days)
    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for current user"
        )
    await set_analytics_cache(cache_key, analytics, expires_seconds=300)
    logging.info("Analytics Cache SET (TTL=300)")

    return analytics

@router.get("/daily-gmv-trend", response_model=DailyGMVTrendResponse, dependencies=[Depends(rate_limit_dependency)])
async def daily_gmv_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days for daily GMV trend"),
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

    cache_key = f"daily-gmv-trend:merchant:{merchant_id}:days:{days}"
    cached = await get_analytics_cache(cache_key)
    if cached:
        print("========== CACHE HIT ==========")
        return cached

    print("========== CACHE MISS ==========")
    trend = await get_daily_gmv_trend(db, current_user.id, days=days)
    if trend is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for current user"
        )
    await set_analytics_cache(cache_key, trend, expires_seconds=300)
    logging.info("Daily GMV Trend Cache SET (TTL=300)")

    return trend

@router.get("/payment-method-breakdown", response_model=PaymentMethodBreakdownResponse, dependencies=[Depends(rate_limit_dependency)])
async def payment_method_breakdown(
    days: int = Query(30, ge=1, le=365, description="Number of days for payment method breakdown"),
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

    cache_key = f"payment-method-breakdown:merchant:{merchant_id}:days:{days}"
    cached = await get_analytics_cache(cache_key)
    if cached:
        print("========== CACHE HIT ==========")
        return cached

    print("========== CACHE MISS ==========")
    breakdown = await get_payment_method_breakdown(db, current_user.id, days=days)
    if breakdown is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for current user"
        )
    await set_analytics_cache(cache_key, breakdown, expires_seconds=300)
    logging.info("Payment Method Breakdown Cache SET (TTL=300)")

    return breakdown

@router.get("/decline-reasons", response_model=DeclineReasonsResponse, dependencies=[Depends(rate_limit_dependency)])
async def decline_reasons(
    days: int = Query(30, ge=1, le=365, description="Number of days for decline reasons"),
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

    cache_key = f"decline-reasons:merchant:{merchant_id}:days:{days}"
    cached = await get_analytics_cache(cache_key)
    if cached:
        print("========== CACHE HIT ==========")
        return cached

    print("========== CACHE MISS ==========")
    from app.services.analytics_service import get_decline_reasons
    reasons = await get_decline_reasons(db, current_user.id, days=days)
    if reasons is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for current user"
        )
    await set_analytics_cache(cache_key, reasons, expires_seconds=300)
    logging.info("Decline Reasons Cache SET (TTL=300)")

    return reasons
