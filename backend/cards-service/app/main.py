import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.database as db
from app.config import settings
from app.routers import admin, cards, health, survey_responses
from app.sync.card_syncer import run_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(application: FastAPI):
    db.pool = await db.create_pool()

    # Weekly sync — every Sunday at 02:00 UTC
    scheduler.add_job(
        run_sync,
        CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="weekly_card_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Card sync scheduler started — runs every Sunday 02:00 UTC")

    yield

    scheduler.shutdown(wait=False)
    await db.pool.close()


app = FastAPI(
    title="WalletAce Cards Service",
    description="Card catalogue management and weekly sync",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(cards.router)
app.include_router(admin.router)
app.include_router(survey_responses.router)
