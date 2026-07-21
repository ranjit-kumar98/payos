from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api import api_router
from app.services.payment_routing_service import PaymentRoutingService
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    root_path="/api"
)

from app.api import setup_kafka_consumer
setup_kafka_consumer(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    async for db in get_db():
        routing_service = PaymentRoutingService(db)
        await routing_service.seed_demo_data()
        break

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_db)):
    try:
        await session.execute(text("SELECT 1"))
        return {"db_status": "ok"}
    except Exception as e:
        return {"error": str(e)}