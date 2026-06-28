from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.services.payment_routing_service import PaymentRoutingService
from app.api.auth import get_current_user
from app.db.session import get_db

router = APIRouter(prefix="/payments", tags=["payments"])

class PaymentRouteRequest(BaseModel):
    amount: float
    currency: str
    payment_method: str

class PaymentRouteResponse(BaseModel):
    selected_gateway: str
    backup_gateway: Optional[str]
    estimated_fee: float
    selection_reason: str

@router.post("/route", response_model=PaymentRouteResponse)
async def route_payment(
    request: PaymentRouteRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    routing_service = PaymentRoutingService(db)
    try:
        result = await routing_service.route_payment(
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result