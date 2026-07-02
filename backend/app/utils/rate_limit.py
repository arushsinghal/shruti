"""Optional request rate limiting helpers."""

import time

from fastapi import HTTPException, Request

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)
    SLOWAPI_AVAILABLE = True
except ImportError:
    RateLimitExceeded = Exception
    _rate_limit_exceeded_handler = None
    SLOWAPI_AVAILABLE = False

    class _NoopLimiter:
        def limit(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

    limiter = _NoopLimiter()


_ATTEMPTS: dict[str, list[float]] = {}


def check_rate_limit(request: Request, key: str, max_attempts: int, window_seconds: int) -> None:
    client_host = request.client.host if request.client else "unknown"
    scoped_key = f"{client_host}:{key}"
    now = time.time()
    cutoff = now - window_seconds
    attempts = [ts for ts in _ATTEMPTS.get(scoped_key, []) if ts >= cutoff]
    if len(attempts) >= max_attempts:
        raise HTTPException(status_code=429, detail="Too many attempts")
    attempts.append(now)
    _ATTEMPTS[scoped_key] = attempts
