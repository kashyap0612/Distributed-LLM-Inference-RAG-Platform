import time
from fastapi import HTTPException
from app.cache.redis_cache import cache
from app.core.config import settings

local: dict[str, tuple[int, float]] = {}

async def enforce_rate_limit(ip: str):
    key = f"rl:{ip}:{int(time.time()//60)}"
    try:
        if cache.force_down or not cache.redis: raise ConnectionError()
        count = await cache.redis.incr(key)
        await cache.redis.expire(key, 70)
    except Exception:
        count, exp = local.get(key, (0, time.time()+70)); count += 1; local[key]=(count, exp)
    if count > settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
