from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.models import Transaction, PaymentMethod, TransactionStatus
from pydantic import BaseModel

router = APIRouter(prefix="/transactions", tags=["transactions"])

class TransactionSummary(BaseModel):
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str
    payment_method: PaymentMethod
    status: TransactionStatus
    gateway_used: Optional[str]
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]
    created_at: datetime

class TransactionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TransactionSummary]

class TransactionDetailResponse(TransactionSummary):
    # Add any additional fields if needed for full detail
    pass

@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    status: Optional[TransactionStatus] = Query(None),
    payment_method: Optional[PaymentMethod] = Query(None),
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    filters = []
    if status:
        filters.append(Transaction.status == status)
    if payment_method:
        filters.append(Transaction.payment_method == payment_method)
    if merchant_id:
        filters.append(Transaction.merchant_id == merchant_id)
    if start_date:
        filters.append(Transaction.created_at >= start_date)
    if end_date:
        filters.append(Transaction.created_at <= end_date)

    query = select(Transaction)
    if filters:
        query = query.where(and_(*filters))
    query = query.order_by(Transaction.created_at.desc())

    total_result = await db.execute(select(Transaction.id).where(and_(*filters)) if filters else select(Transaction.id))
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    transactions = result.scalars().all()

    items = [
        TransactionSummary(
            transaction_id=str(t.id),
            merchant_id=str(t.merchant_id),
            amount=float(t.amount),
            currency=t.currency,
            payment_method=t.payment_method,
            status=t.status,
            gateway_used=t.gateway_used,
            razorpay_order_id=t.razorpay_order_id,
            razorpay_payment_id=t.razorpay_payment_id,
            created_at=t.created_at
        )
        for t in transactions
    ]

    return TransactionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )

@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        uuid_obj = UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction_id format")

    query = select(Transaction).where(Transaction.id == uuid_obj)
    result = await db.execute(query)
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionDetailResponse(
        transaction_id=str(transaction.id),
        merchant_id=str(transaction.merchant_id),
        amount=float(transaction.amount),
        currency=transaction.currency,
        payment_method=transaction.payment_method,
        status=transaction.status,
        gateway_used=transaction.gateway_used,
        razorpay_order_id=transaction.razorpay_order_id,
        razorpay_payment_id=transaction.razorpay_payment_id,
        created_at=transaction.created_at
    )