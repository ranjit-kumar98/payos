from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from starlette.responses import JSONResponse
from sqlalchemy import text

app = FastAPI()

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