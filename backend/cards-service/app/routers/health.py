import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from app import __version__
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(conn: asyncpg.Connection = Depends(get_db)):
    try:
        await conn.fetchval("SELECT 1")
        db_status = "connected"
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}")

    return {
        "status": "ok",
        "version": __version__,
        "db": db_status,
    }
