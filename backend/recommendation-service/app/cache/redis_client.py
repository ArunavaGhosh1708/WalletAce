"""
Upstash Redis session cache.

Stores the UserSurvey JSON ephemerally during recommendation processing.
Key  : session:{uuid}
Value: serialized UserSurvey JSON
TTL  : 30 minutes (1800 seconds)

No PII is persisted beyond this window.
"""

import json

from redis.asyncio import Redis

from app.models.survey import UserSurvey

SESSION_TTL = 1800  # 30 minutes


class RedisClient:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def set_session(self, session_id: str, survey: UserSurvey) -> None:
        """
        Persist the survey for this session.
        Silently swallows errors so a Redis outage never blocks a recommendation.
        """
        try:
            await self._redis.setex(
                name=f"session:{session_id}",
                time=SESSION_TTL,
                value=survey.model_dump_json(),
            )
        except Exception:
            # Redis is non-critical; recommendation proceeds regardless
            pass

    async def get_session(self, session_id: str) -> UserSurvey | None:
        """
        Retrieve a previously stored survey by session ID.
        Returns None if the key is expired or Redis is unavailable.
        """
        try:
            raw = await self._redis.get(f"session:{session_id}")
            if raw is None:
                return None
            return UserSurvey(**json.loads(raw))
        except Exception:
            return None

    async def delete_session(self, session_id: str) -> None:
        """Remove the session key so stale survey data is never returned."""
        try:
            await self._redis.delete(f"session:{session_id}")
        except Exception:
            pass

    async def close(self) -> None:
        await self._redis.aclose()


def make_redis_client(redis_url: str) -> RedisClient:
    """Create a RedisClient from a rediss:// or redis:// URL."""
    redis = Redis.from_url(redis_url, decode_responses=True)
    return RedisClient(redis)
