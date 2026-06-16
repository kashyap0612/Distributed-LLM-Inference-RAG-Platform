import hashlib, json, time
from redis.asyncio import Redis
from app.core.config import settings
from app.observability.metrics import CACHE

class Cache:
    def __init__(self):
        self.redis: Redis | None = None
        self.local: dict[str, tuple[float, str]] = {}
        self.force_down = False

    async def connect(self):
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    def key(self, layer: str, value: str) -> str:
        return f"{layer}:{hashlib.sha256(value.encode()).hexdigest()}"

    async def get_json(self, layer: str, value: str):
        key = self.key(layer, value)
        try:
            if self.force_down: raise ConnectionError("simulated redis failure")
            raw = await self.redis.get(key) if self.redis else None
        except Exception:
            item = self.local.get(key); raw = item[1] if item and item[0] > time.time() else None
        CACHE.labels(layer, "hit" if raw else "miss").inc()
        return json.loads(raw) if raw else None

    async def set_json(self, layer: str, value: str, payload, ttl: int | None = None):
        raw = json.dumps(payload); key = self.key(layer, value); ttl = ttl or settings.cache_ttl_seconds
        try:
            if self.force_down: raise ConnectionError("simulated redis failure")
            if self.redis: await self.redis.setex(key, ttl, raw)
        except Exception:
            self.local[key] = (time.time() + ttl, raw)

cache = Cache()
