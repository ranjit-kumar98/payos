from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.schemas.dispute import DisputeCreate, Dispute, DisputeList, DisputeStatus, DisputeReason
from app.services.dispute_service import DisputeService
from app.db.session import get_db

router = APIRouter()


@router.post("", response_model=Dispute, status_code=status.HTTP_201_CREATED)
async def raise_dispute(
    dispute_in: DisputeCreate,
    db: AsyncSession = Depends(get_db),
):
    service = DisputeService(db)
    try:
        dispute = await service.raise_dispute(
            transaction_id=dispute_in.transaction_id,
            reason=dispute_in.reason,
            description=dispute_in.description,
        )
    except ValueError as e:
        # Transaction not found or invalid status
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        # Dispute already exists
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return dispute


@router.get("", response_model=DisputeList)
async def list_disputes(
    status: Optional[DisputeStatus] = None,
    merchant_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    service = DisputeService(db)
    disputes = await service.list_disputes(status=status, merchant_id=merchant_id)
    return DisputeList(disputes=disputes, total=len(disputes))


@router.get("/{dispute_id}", response_model=Dispute)
async def get_dispute(dispute_id: UUID, db: AsyncSession = Depends(get_db)):
    service = DisputeService(db)
    dispute = await service.get_dispute(dispute_id)
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")
    return dispute


@router.post("/{dispute_id}/review", response_model=Dispute)
async def move_to_review(dispute_id: UUID, db: AsyncSession = Depends(get_db)):
    service = DisputeService(db)
    try:
        dispute = await service.move_to_review(dispute_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return dispute


@router.post("/{dispute_id}/resolve", response_model=Dispute)
async def resolve_dispute(dispute_id: UUID, resolution_notes: str, db: AsyncSession = Depends(get_db)):
    service = DisputeService(db)
    if not resolution_notes or resolution_notes.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="resolution_notes is required and must not be empty")
    try:
        dispute = await service.resolve_dispute(dispute_id, resolution_notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return dispute


@router.post("/{dispute_id}/reject", response_model=Dispute)
async def reject_dispute(dispute_id: UUID, resolution_notes: str, db: AsyncSession = Depends(get_db)):
    service = DisputeService(db)
    if not resolution_notes or resolution_notes.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="resolution_notes is required and must not be empty")
    try:
        dispute = await service.reject_dispute(dispute_id, resolution_notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return dispute