from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.db.session import get_db
from app.schemas.analytics import AnalyticsOverviewResponse
from app.services.analytics_service import get_merchant_analytics

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def analytics_overview(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analytics = await get_merchant_analytics(db, current_user.id)
    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for current user"
        )
    return analytics
