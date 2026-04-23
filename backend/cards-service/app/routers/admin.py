import asyncio

from fastapi import APIRouter, BackgroundTasks

from app.sync.card_syncer import run_sync

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/sync", summary="Trigger card catalogue sync manually")
async def trigger_sync(background_tasks: BackgroundTasks) -> dict:
    """
    Kicks off the DeepSeek card sync in the background and returns immediately.
    Check Cloud Run logs for progress and final upsert count.
    """
    background_tasks.add_task(run_sync)
    return {"status": "sync started", "message": "Check logs for progress"}
