
from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.logout import router as logout_router
from app.api.payment_router import router as payment_router
from app.api.webhooks import router as webhooks_router
from app.api.transaction_router import router as transaction_router
from app.api.fraud import router as fraud_router   # <-- ADD
from app.api.fraud_report import router as fraud_report_router  # <-- ADD
from app.api.bnpl_router import router as bnpl_router  # <-- ADD
from app.api.internal_kafka_test import router as internal_kafka_test_router
from app.api import analytics

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(logout_router)
api_router.include_router(payment_router)
api_router.include_router(webhooks_router)
api_router.include_router(transaction_router)
api_router.include_router(fraud_router)            # <-- ADD
api_router.include_router(fraud_report_router)     # <-- ADD
api_router.include_router(bnpl_router)             # <-- ADD
api_router.include_router(internal_kafka_test_router)
from app.api.internal_celery_test import router as internal_celery_test_router
api_router.include_router(internal_celery_test_router, prefix="/internal", tags=["internal"])

api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Register dispute router
from app.api.dispute_router import router as dispute_router
api_router.include_router(dispute_router, prefix="/disputes", tags=["disputes"])

import asyncio
from fastapi import FastAPI
from app.services.kafka.consumer import KafkaConsumerService

def setup_kafka_consumer(app: FastAPI):
    consumer_service = KafkaConsumerService()

    @app.on_event("startup")
    async def start_kafka_consumer():
        await consumer_service.start()

    @app.on_event("shutdown")
    async def stop_kafka_consumer():
        await consumer_service.stop()
