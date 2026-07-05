"""Redis client wrapper with in-memory fallback."""

from typing import Optional

from redis import Redis

from app.core.config import settings


class MockRedis:
    """In-memory Redis replacement when Redis server is unavailable."""

    def __init__(self):
        self._data: dict = {}

    def hset(self, key: str, field: str, value: str | int) -> int:
        if key not in self._data:
            self._data[key] = {}
        if not isinstance(self._data[key], dict):
            self._data[key] = {}
        self._data[key][str(field)] = str(value)
        return 1

    def hget(self, key: str, field: str) -> Optional[str]:
        bucket = self._data.get(key, {})
        if isinstance(bucket, dict):
            return bucket.get(str(field))
        return None

    def sadd(self, key: str, *values: str) -> int:
        if key not in self._data:
            self._data[key] = set()
        if not isinstance(self._data[key], set):
            self._data[key] = set()
        count = 0
        for v in values:
            if v not in self._data[key]:
                self._data[key].add(v)
                count += 1
        return count

    def smembers(self, key: str) -> set:
        val = self._data.get(key, set())
        return val if isinstance(val, set) else set()

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                count += 1
        return count

    def expire(self, key: str, ttl: int) -> bool:
        return True

    def setex(self, key: str, ttl: int, value: str) -> bool:
        self._data[key] = {"_val": value}
        return True

    def get(self, key: str) -> Optional[str]:
        val = self._data.get(key, {})
        if isinstance(val, dict):
            return val.get("_val")
        return None

    def ping(self) -> bool:
        return True


try:
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=3)
    redis_client.ping()
except Exception:
    redis_client = MockRedis()


def get_redis() -> MockRedis | Redis:
    return redis_client
