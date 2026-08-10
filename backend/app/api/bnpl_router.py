from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models import BnplLoan, BnplStatus
from app.schemas.bnpl import (
    BnplLoanCreateRequest,
    BnplLoanResponse,
)
from app.services.bnpl_service import BnplService


router = APIRouter(
    prefix="/bnpl",
    tags=["bnpl"],
)


@router.post(
    "/loans",
    response_model=BnplLoanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_bnpl_loan(
    request: BnplLoanCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Validate eligibility and calculate EMI/schedule
    try:
        calculation = BnplService.calculate_reducing_balance_emi(
            principal=request.principal,
            tenure=request.tenure,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 2. Convert Decimal repayment values to JSON-safe strings
    repayment_schedule = [
        {
            "month": entry.month,
            "emi": str(entry.emi),
            "interest": str(entry.interest),
            "principal": str(entry.principal),
            "remaining_balance": str(entry.remaining_balance),
        }
        for entry in calculation.repayment_schedule
    ]

    # 3. Create loan atomically
    async with db.begin():
        loan = BnplLoan(
            user_id=str(current_user.id),
            transaction_id=request.transaction_id,
            principal=float(calculation.principal),
            tenure_months=calculation.tenure,
            interest_rate_pa=float(calculation.annual_interest_rate),
            emi_amount=float(calculation.monthly_emi),
            total_interest=float(calculation.total_interest),
            total_payable=float(calculation.total_repayment),
            status=BnplStatus.ACTIVE,
            repayment_schedule=repayment_schedule,
            created_at=datetime.utcnow(),
        )

        db.add(loan)
        await db.flush()

    # 4. Build API response explicitly
    return BnplLoanResponse(
        id=str(loan.id),
        principal=calculation.principal,
        tenure_months=calculation.tenure,
        annual_interest_rate=calculation.annual_interest_rate,
        monthly_emi=calculation.monthly_emi,
        total_interest=calculation.total_interest,
        total_repayment=calculation.total_repayment,
        status=loan.status.value,
        repayment_schedule=repayment_schedule,
        created_at=loan.created_at,
    )


@router.get(
    "/loans",
    response_model=List[BnplLoanResponse],
)
async def get_user_loans(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BnplLoan).where(
            BnplLoan.user_id == str(current_user.id)
        )
    )

    loans = result.scalars().all()

    responses = []

    for loan in loans:
        schedule = loan.repayment_schedule or []

        responses.append(
            BnplLoanResponse(
                id=str(loan.id),
                principal=Decimal(str(loan.principal)),
                tenure_months=loan.tenure_months,
                annual_interest_rate=Decimal(str(loan.interest_rate_pa)),
                monthly_emi=Decimal(str(loan.emi_amount)),
                total_interest=Decimal(str(loan.total_interest)),
                total_repayment=Decimal(str(loan.total_payable)),
                status=loan.status.value,
                repayment_schedule=schedule,
                created_at=loan.created_at,
            )
        )

    return responses