from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends, HTTPException
from app.db.session import get_db
from app.api import api_router

app = FastAPI(
    root_path="/api"
)

app.include_router(api_router)

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