from .payments import router as payments_router
from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.logout import router as logout_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(logout_router)
api_router.include_router(payments_router)


