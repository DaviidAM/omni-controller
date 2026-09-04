"""Simple in-memory sliding window rate limiter."""
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_buckets: dict[str, list[float]] = defaultdict(list)


def get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For (for tunnel/proxy setups)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(bucket_key: str, max_requests: int, window_seconds: int = 60) -> None:
    """Sliding window rate limit. Raises HTTPException(429) when exceeded."""
    now = time.monotonic()
    cutoff = now - window_seconds
    bucket = _buckets[bucket_key]
    # Drop expired entries
    _buckets[bucket_key] = bucket = [t for t in bucket if t > cutoff]

    if len(bucket) >= max_requests:
        oldest = bucket[0]
        retry_after = max(1, int(window_seconds - (now - oldest)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({max_requests} req/{window_seconds}s). Retry in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


def reset_rate_limits() -> None:
    """For tests only — clears all rate limit state."""
    _buckets.clear()
