from typing import AsyncGenerator

import asyncpg

from app.config import settings

pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    # asyncpg only accepts postgresql:// — strip SQLAlchemy's +asyncpg driver prefix
    dsn = settings.database_url.replace("+asyncpg", "")
    return await asyncpg.create_pool(
        dsn=dsn,
        min_size=2,
        max_size=10,
    )


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    async with pool.acquire() as conn:
        yield conn
