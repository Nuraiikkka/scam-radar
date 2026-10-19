import threading
import time

import redis
from fastapi import Request

from app.errors import AppError
from app.settings.conf import settings


class MemoryCounter:
    def __init__(self):
        self.lock = threading.Lock()
        self.counts = {}

    def hit(self, key: str, window_seconds: int) -> int:
        now = time.time()
        with self.lock:
            count, expires_at = self.counts.get(key, (0, now + window_seconds))
            if now >= expires_at:
                count = 0
                expires_at = now + window_seconds
            count = count + 1
            self.counts[key] = (count, expires_at)
            return count

    def reset(self) -> None:
        with self.lock:
            self.counts = {}


class RedisCounter:
    def __init__(self, url: str):
        self.client = redis.Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)

    def hit(self, key: str, window_seconds: int) -> int:
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        result = pipe.execute()
        return int(result[0])

    def reset(self) -> None:
        for key in self.client.scan_iter("ratelimit:*"):
            self.client.delete(key)


def make_counter():
    if settings.rate_limit_storage == "memory":
        return MemoryCounter()
    return RedisCounter(settings.redis_url)


counter = make_counter()


def client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-real-ip")
        if forwarded:
            return forwarded.strip()
    if request.client is None:
        return "unknown"
    return request.client.host


def check_limit(key: str, limit: int, window_seconds: int = 3600) -> None:
    try:
        count = counter.hit("ratelimit:" + key, window_seconds)
    except redis.RedisError:
        raise AppError("service_unavailable", "Rate limiter is unavailable, try again later", 503)
    if count > limit:
        raise AppError("rate_limited", "Too many requests, please try again later", 429)


def limit_analyze(request: Request, user_id: int | None) -> None:
    if user_id is None:
        check_limit("analyze:ip:" + client_ip(request), settings.rate_limit_anonymous_per_hour)
    else:
        check_limit("analyze:user:" + str(user_id), settings.rate_limit_user_per_hour)


def limit_auth(request: Request) -> None:
    check_limit("auth:ip:" + client_ip(request), settings.rate_limit_auth_per_hour)
