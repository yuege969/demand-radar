from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Callable, Awaitable
from typing import TypeVar

import httpx
from loguru import logger

T = TypeVar("T")


class RateLimiter:
    """Enforces jittered delays and concurrency limits between outbound requests."""

    def __init__(
        self,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        max_retries: int = 3,
        backoff_base: float = 2.0,
        max_concurrent: int = 2,
    ):
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """Acquire the semaphore then sleep for a jittered delay."""
        await self._semaphore.acquire()
        try:
            async with self._lock:
                elapsed = time.monotonic() - self._last_request_time
                if elapsed < self._min_delay:
                    await asyncio.sleep(self._min_delay - elapsed)
                jitter = random.uniform(0, self._max_delay - self._min_delay)
                await asyncio.sleep(jitter)
                self._last_request_time = time.monotonic()
        except Exception:
            self._semaphore.release()
            raise

    def release(self) -> None:
        try:
            self._semaphore.release()
        except Exception:
            pass

    async def execute_with_retry(
        self,
        fn: Callable[[], Awaitable[T]],
    ) -> T:
        """Execute an async request with jittered delays and exponential backoff on retryable errors."""
        last_exc: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                await self.wait()
                result = await fn()
                self.release()
                return result
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                self.release()
                last_exc = e
                status = getattr(e, "response", None)
                status_code = status.status_code if status is not None else None

                if status_code in (429, 503) or isinstance(e, (httpx.ConnectError, httpx.RemoteProtocolError)):
                    if attempt < self._max_retries:
                        backoff = self._backoff_base ** (attempt + 1) + random.uniform(0, 1)
                        logger.warning(
                            "Request failed (attempt {}/{}), retrying in {:.1f}s: {}",
                            attempt + 1, self._max_retries, backoff, e,
                        )
                        await asyncio.sleep(backoff)
                        continue
                raise
            except Exception:
                self.release()
                raise

        raise last_exc  # type: ignore[misc]


def create_rate_limiter() -> RateLimiter:
    from app.config import settings

    return RateLimiter(
        min_delay=settings.CRAWL_MIN_DELAY,
        max_delay=settings.CRAWL_MAX_DELAY,
        max_retries=settings.CRAWL_MAX_RETRIES,
        backoff_base=settings.CRAWL_BACKOFF_BASE,
        max_concurrent=settings.CRAWL_RATE_LIMIT_CONCURRENT,
    )
