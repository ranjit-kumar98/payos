from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.logout import router as logout_router
from app.api.payment_router import router as payment_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(logout_router)
api_router.include_router(payment_router)


