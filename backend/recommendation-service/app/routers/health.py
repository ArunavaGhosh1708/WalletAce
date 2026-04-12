import httpx
from fastapi import APIRouter, HTTPException

from app import __version__
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    # Verify cards-service is reachable
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.cards_service_url}/health")
            resp.raise_for_status()
            cards_status = "reachable"
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cards service unavailable: {e}")

    return {
        "status": "ok",
        "version": __version__,
        "cards_service": cards_status,
    }
