import redis
from fastapi import Request
from app.config.config import Settings

_settings = Settings()


def create_redis_client() -> redis.Redis:
    """Create a Redis client with a connection pool. Call once at startup."""
    return redis.Redis.from_url(_settings.REDIS_URL, decode_responses=True)


def get_redis(request: Request) -> redis.Redis:
    """FastAPI dependency — returns the shared pool held in app.state."""
    return request.app.state.redis
