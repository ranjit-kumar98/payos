from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.logout import router as logout_router
from app.api.payment_router import router as payment_router
from app.api.webhooks import router as webhooks_router
from app.api.transaction_router import router as transaction_router
from app.api.fraud import router as fraud_router   # <-- ADD

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(logout_router)
api_router.include_router(payment_router)
api_router.include_router(webhooks_router)
api_router.include_router(transaction_router)
api_router.include_router(fraud_router)            # <-- ADD
