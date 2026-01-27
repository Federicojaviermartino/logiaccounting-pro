"""
Rate Limiting Middleware
Implements request rate limiting to protect against abuse and DoS attacks.
"""

import time
import hashlib
from typing import Optional, Dict, List, Callable, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitRule:
    """Configuration for a rate limit rule."""
    requests: int
    window_seconds: int
    key_func: Optional[Callable[[Request], str]] = None
    methods: Optional[List[str]] = None
    paths: Optional[List[str]] = None
    path_prefix: Optional[str] = None


@dataclass
class RateLimitEntry:
    """Tracks rate limit state for a key."""
    count: int = 0
    window_start: float = 0.0
    tokens: float = 0.0
    last_update: float = 0.0
    request_times: List[float] = field(default_factory=list)


class RateLimitStore:
    """In-memory rate limit storage."""

    def __init__(self):
        self._data: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._cleanup_interval = 300
        self._last_cleanup = time.time()

    def get(self, key: str) -> RateLimitEntry:
        """Get rate limit entry for a key."""
        return self._data[key]

    def set(self, key: str, entry: RateLimitEntry):
        """Set rate limit entry for a key."""
        self._data[key] = entry

    def cleanup(self, max_age: float = 3600):
        """Remove expired entries."""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        expired_keys = [
            key for key, entry in self._data.items()
            if current_time - entry.last_update > max_age
        ]
        for key in expired_keys:
            del self._data[key]

        self._last_cleanup = current_time


class RateLimiter:
    """Rate limiter implementation with multiple algorithms."""

    def __init__(
        self,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        store: Optional[RateLimitStore] = None,
    ):
        self.algorithm = algorithm
        self.store = store or RateLimitStore()

    def check_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Returns:
            Tuple of (is_allowed, remaining, reset_time)
        """
        if self.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return self._check_fixed_window(key, limit, window_seconds)
        elif self.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return self._check_sliding_window(key, limit, window_seconds)
        elif self.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return self._check_token_bucket(key, limit, window_seconds)
        else:
            return self._check_leaky_bucket(key, limit, window_seconds)

    def _check_fixed_window(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """Fixed window rate limiting."""
        current_time = time.time()
        entry = self.store.get(key)

        window_start = int(current_time / window_seconds) * window_seconds

        if entry.window_start != window_start:
            entry.window_start = window_start
            entry.count = 0

        entry.count += 1
        entry.last_update = current_time
        self.store.set(key, entry)

        remaining = max(0, limit - entry.count)
        reset_time = int(window_start + window_seconds - current_time)
        is_allowed = entry.count <= limit

        return is_allowed, remaining, reset_time

    def _check_sliding_window(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """Sliding window rate limiting."""
        current_time = time.time()
        entry = self.store.get(key)

        window_start = current_time - window_seconds
        entry.request_times = [
            t for t in entry.request_times if t > window_start
        ]

        entry.request_times.append(current_time)
        entry.last_update = current_time
        self.store.set(key, entry)

        count = len(entry.request_times)
        remaining = max(0, limit - count)

        if entry.request_times:
            oldest = entry.request_times[0]
            reset_time = int(oldest + window_seconds - current_time)
        else:
            reset_time = window_seconds

        is_allowed = count <= limit

        return is_allowed, remaining, max(0, reset_time)

    def _check_token_bucket(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """Token bucket rate limiting."""
        current_time = time.time()
        entry = self.store.get(key)

        refill_rate = limit / window_seconds

        if entry.last_update == 0:
            entry.tokens = float(limit)
            entry.last_update = current_time
        else:
            elapsed = current_time - entry.last_update
            entry.tokens = min(float(limit), entry.tokens + elapsed * refill_rate)
            entry.last_update = current_time

        is_allowed = entry.tokens >= 1.0
        if is_allowed:
            entry.tokens -= 1.0

        self.store.set(key, entry)

        remaining = int(entry.tokens)
        tokens_needed = 1.0 - entry.tokens if entry.tokens < 1.0 else 0
        reset_time = int(tokens_needed / refill_rate) if tokens_needed > 0 else 0

        return is_allowed, remaining, reset_time

    def _check_leaky_bucket(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """Leaky bucket rate limiting."""
        current_time = time.time()
        entry = self.store.get(key)

        leak_rate = limit / window_seconds

        if entry.last_update == 0:
            entry.tokens = 0.0
            entry.last_update = current_time
        else:
            elapsed = current_time - entry.last_update
            entry.tokens = max(0.0, entry.tokens - elapsed * leak_rate)
            entry.last_update = current_time

        is_allowed = entry.tokens < float(limit)
        if is_allowed:
            entry.tokens += 1.0

        self.store.set(key, entry)

        remaining = max(0, int(float(limit) - entry.tokens))
        overflow = entry.tokens - float(limit) if entry.tokens > float(limit) else 0
        reset_time = int(overflow / leak_rate) if overflow > 0 else 0

        return is_allowed, remaining, reset_time


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    if request.client:
        return request.client.host

    return "unknown"


def get_user_id(request: Request) -> Optional[str]:
    """Extract user ID from request if authenticated."""
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user.get("id")
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI applications.

    Features:
    - Multiple rate limiting algorithms
    - Per-IP and per-user limiting
    - Configurable rules for different endpoints
    - Rate limit headers in responses
    """

    def __init__(
        self,
        app,
        default_limit: int = 100,
        default_window: int = 60,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        rules: Optional[List[RateLimitRule]] = None,
        excluded_paths: Optional[List[str]] = None,
        key_prefix: str = "ratelimit",
        enable_headers: bool = True,
        store: Optional[RateLimitStore] = None,
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        self.algorithm = algorithm
        self.rules = rules or []
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.key_prefix = key_prefix
        self.enable_headers = enable_headers
        self.limiter = RateLimiter(algorithm, store or RateLimitStore())

    def _get_rule_for_request(self, request: Request) -> Optional[RateLimitRule]:
        """Find matching rule for the request."""
        path = request.url.path
        method = request.method

        for rule in self.rules:
            if rule.methods and method not in rule.methods:
                continue

            if rule.paths and path not in rule.paths:
                continue

            if rule.path_prefix and not path.startswith(rule.path_prefix):
                continue

            return rule

        return None

    def _get_rate_limit_key(self, request: Request, rule: Optional[RateLimitRule]) -> str:
        """Generate rate limit key for the request."""
        if rule and rule.key_func:
            custom_key = rule.key_func(request)
            if custom_key:
                return f"{self.key_prefix}:{custom_key}"

        user_id = get_user_id(request)
        if user_id:
            return f"{self.key_prefix}:user:{user_id}"

        client_ip = get_client_ip(request)
        path_hash = hashlib.md5(request.url.path.encode()).hexdigest()[:8]
        return f"{self.key_prefix}:ip:{client_ip}:{path_hash}"

    def _should_apply_limit(self, request: Request) -> bool:
        """Check if rate limiting should be applied to this request."""
        path = request.url.path
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return False
        return True

    def _add_rate_limit_headers(
        self,
        response: Response,
        limit: int,
        remaining: int,
        reset: int,
    ):
        """Add rate limit headers to response."""
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request with rate limiting."""
        if not self._should_apply_limit(request):
            return await call_next(request)

        rule = self._get_rule_for_request(request)
        limit = rule.requests if rule else self.default_limit
        window = rule.window_seconds if rule else self.default_window

        key = self._get_rate_limit_key(request, rule)
        is_allowed, remaining, reset = self.limiter.check_limit(key, limit, window)

        self.limiter.store.cleanup()

        if not is_allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": reset,
                },
            )
            if self.enable_headers:
                self._add_rate_limit_headers(response, limit, 0, reset)
            response.headers["Retry-After"] = str(reset)
            return response

        response = await call_next(request)

        if self.enable_headers:
            self._add_rate_limit_headers(response, limit, remaining, reset)

        return response


class RateLimitConfig:
    """Builder class for rate limit configuration."""

    def __init__(self):
        self.default_limit = 100
        self.default_window = 60
        self.algorithm = RateLimitAlgorithm.SLIDING_WINDOW
        self.rules: List[RateLimitRule] = []
        self.excluded_paths: List[str] = []
        self.key_prefix = "ratelimit"
        self.enable_headers = True

    def set_default_limit(self, requests: int, window_seconds: int) -> "RateLimitConfig":
        """Set default rate limit."""
        self.default_limit = requests
        self.default_window = window_seconds
        return self

    def set_algorithm(self, algorithm: RateLimitAlgorithm) -> "RateLimitConfig":
        """Set rate limiting algorithm."""
        self.algorithm = algorithm
        return self

    def add_rule(self, rule: RateLimitRule) -> "RateLimitConfig":
        """Add a rate limit rule."""
        self.rules.append(rule)
        return self

    def add_path_rule(
        self,
        path_prefix: str,
        requests: int,
        window_seconds: int,
        methods: Optional[List[str]] = None,
    ) -> "RateLimitConfig":
        """Add a path-based rate limit rule."""
        self.rules.append(RateLimitRule(
            requests=requests,
            window_seconds=window_seconds,
            path_prefix=path_prefix,
            methods=methods,
        ))
        return self

    def exclude_path(self, path: str) -> "RateLimitConfig":
        """Exclude a path from rate limiting."""
        self.excluded_paths.append(path)
        return self

    def build(self) -> dict:
        """Build the configuration dictionary."""
        return {
            "default_limit": self.default_limit,
            "default_window": self.default_window,
            "algorithm": self.algorithm,
            "rules": self.rules,
            "excluded_paths": self.excluded_paths if self.excluded_paths else None,
            "key_prefix": self.key_prefix,
            "enable_headers": self.enable_headers,
        }
