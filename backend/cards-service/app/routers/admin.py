from fastapi import APIRouter

from app.sync.card_syncer import run_sync

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/sync", summary="Trigger card catalogue sync manually")
async def trigger_sync() -> dict:
    """
    Runs the DeepSeek card sync immediately.
    Same operation as the weekly cron — upserts all 48 cards.
    """
    return await run_sync()
