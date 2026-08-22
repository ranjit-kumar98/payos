from datetime import datetime
from decimal import Decimal
from typing import List

import logging
from app.services.kafka.producer import KafkaProducerService

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models import BnplLoan, BnplStatus
from app.schemas.bnpl import (
    BnplLoanCreateRequest,
    BnplLoanResponse,
    BnplEligibilityRequest,
    BnplEligibilityResponse,
    BnplCalculateRequest,
    BnplCalculateResponse,
)
from app.services.bnpl_service import BnplService


router = APIRouter(
    prefix="/bnpl",
    tags=["bnpl"],
)

@router.post(
    "/eligibility",
    response_model=BnplEligibilityResponse,
)
async def check_bnpl_eligibility(
    request: BnplEligibilityRequest,
    current_user=Depends(get_current_user),
):
    try:
        BnplService.validate_eligibility(
            principal=request.principal,
            tenure=request.tenure,
        )

        return BnplEligibilityResponse(
            eligible=True,
            message="BNPL is eligible for the requested amount and tenure.",
        )

    except ValueError as exc:
        return BnplEligibilityResponse(
            eligible=False,
            message=str(exc),
        )
@router.post(
    "/calculate",
    response_model=BnplCalculateResponse,
)
async def calculate_bnpl(
    request: BnplCalculateRequest,
    current_user=Depends(get_current_user),
):
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

    repayment_schedule = [
        {
            "month": entry.month,
            "emi": entry.emi,
            "interest": entry.interest,
            "principal": entry.principal,
            "remaining_balance": entry.remaining_balance,
        }
        for entry in calculation.repayment_schedule
    ]

    return BnplCalculateResponse(
        principal=calculation.principal,
        tenure=calculation.tenure,
        annual_interest_rate=calculation.annual_interest_rate,
        monthly_emi=calculation.monthly_emi,
        total_interest=calculation.total_interest,
        total_repayment=calculation.total_repayment,
        repayment_schedule=repayment_schedule,
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

        payload = {
            "loan_id": str(loan.id),
            "user_id": str(current_user.id),
            "customer_email": current_user.email,
            "customer_name": getattr(current_user, "full_name", None) or "Customer",
            "transaction_id": request.transaction_id,
            "principal": str(calculation.principal),
            "tenure_months": calculation.tenure,
            "annual_interest_rate": str(calculation.annual_interest_rate),
            "monthly_emi": str(calculation.monthly_emi),
            "total_interest": str(calculation.total_interest),
            "total_repayment": str(calculation.total_repayment),
            "status": BnplStatus.ACTIVE.value,
            "repayment_schedule": repayment_schedule,
        }

    kafka_producer = KafkaProducerService()
    try:
        await kafka_producer.publish(
            topic="bnpl.loan_created",
            event_type="bnpl.loan_created",
            payload=payload,
            correlation_id=str(loan.id),
        )
        logging.info("BNPL loan created Kafka event published")
    except Exception as e:
        logging.error(f"Failed to publish BNPL loan created event: {e}")

    # 4. Build API response explicitly
    return BnplLoanResponse(
        id=str(loan.id),
        principal=Decimal(str(loan.principal)),
        tenure_months=loan.tenure_months,
        annual_interest_rate=Decimal(str(loan.interest_rate_pa)),
        monthly_emi=Decimal(str(loan.emi_amount)),
        total_interest=Decimal(str(loan.total_interest)),
        total_repayment=Decimal(str(loan.total_payable)),
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
