from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache.redis_client import make_redis_client
from app.config import settings
from app.routers import health, recommend


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Shared HTTP client for all outbound calls to cards-service
    application.state.http_client = httpx.AsyncClient()

    # Redis client for session caching
    application.state.redis = make_redis_client(settings.redis_url)

    yield

    await application.state.http_client.aclose()
    await application.state.redis.close()


app = FastAPI(
    title="WalletAce Recommendation Service",
    description="3-phase credit card recommendation engine",
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
app.include_router(recommend.router)
