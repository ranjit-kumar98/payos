
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api.auth import get_current_user
from app.db.session import get_db
from app.services.fraud_report_service import get_fraud_reports
from app.schemas.fraud_report import FraudReportResponse


router = APIRouter(
    prefix="/fraud-reports",
    tags=["fraud-reports"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[FraudReportResponse])
async def read_fraud_reports(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    reports = await get_fraud_reports(db)
    if not reports:
        return []
    return reports
