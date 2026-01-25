"""
Rate limiting implementation for LogiAccounting Pro.
"""

import time
import asyncio
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import threading


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithm types."""

    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit."""

    name: str
    requests: int
    window_seconds: int
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    burst_size: Optional[int] = None
    penalty_seconds: int = 0
    exclude_paths: List[str] = field(default_factory=list)
    apply_to_authenticated_only: bool = False
    apply_to_anonymous_only: bool = False
    group_by: str = "ip"


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after_seconds: Optional[int] = None
    rule_name: Optional[str] = None

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_at.timestamp())),
        }
        if self.retry_after_seconds:
            headers["Retry-After"] = str(self.retry_after_seconds)
        return headers


class SlidingWindowCounter:
    """Sliding window counter implementation."""

    def __init__(self, window_seconds: int, max_requests: int):
        self._window_seconds = window_seconds
        self._max_requests = max_requests
        self._buckets: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        self._lock = threading.Lock()

    def _cleanup_old_entries(self, key: str, current_time: float) -> None:
        """Remove entries older than the window."""
        cutoff = current_time - self._window_seconds
        self._buckets[key] = [
            (ts, count) for ts, count in self._buckets[key]
            if ts > cutoff
        ]

    def increment(self, key: str, amount: int = 1) -> Tuple[bool, int, int]:
        """Increment counter and check if within limit."""
        current_time = time.time()

        with self._lock:
            self._cleanup_old_entries(key, current_time)

            current_count = sum(count for _, count in self._buckets[key])

            if current_count + amount > self._max_requests:
                return False, current_count, self._max_requests - current_count

            self._buckets[key].append((current_time, amount))
            return True, current_count + amount, self._max_requests - current_count - amount

    def get_count(self, key: str) -> int:
        """Get current count for a key."""
        current_time = time.time()

        with self._lock:
            self._cleanup_old_entries(key, current_time)
            return sum(count for _, count in self._buckets[key])

    def reset(self, key: str) -> None:
        """Reset counter for a key."""
        with self._lock:
            self._buckets[key] = []

    def get_reset_time(self, key: str) -> datetime:
        """Get when the oldest entry will expire."""
        current_time = time.time()

        with self._lock:
            self._cleanup_old_entries(key, current_time)

            if not self._buckets[key]:
                return datetime.utcnow()

            oldest = min(ts for ts, _ in self._buckets[key])
            reset_time = oldest + self._window_seconds
            return datetime.utcfromtimestamp(reset_time)


class TokenBucket:
    """Token bucket rate limiter implementation."""

    def __init__(self, capacity: int, refill_rate: float):
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens: Dict[str, float] = {}
        self._last_refill: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _refill(self, key: str, current_time: float) -> float:
        """Refill tokens based on time elapsed."""
        if key not in self._last_refill:
            self._tokens[key] = self._capacity
            self._last_refill[key] = current_time
            return self._capacity

        elapsed = current_time - self._last_refill[key]
        new_tokens = elapsed * self._refill_rate
        self._tokens[key] = min(self._capacity, self._tokens.get(key, 0) + new_tokens)
        self._last_refill[key] = current_time

        return self._tokens[key]

    def consume(self, key: str, tokens: int = 1) -> Tuple[bool, float]:
        """Try to consume tokens."""
        current_time = time.time()

        with self._lock:
            available = self._refill(key, current_time)

            if available >= tokens:
                self._tokens[key] = available - tokens
                return True, self._tokens[key]

            return False, available

    def get_tokens(self, key: str) -> float:
        """Get current token count."""
        current_time = time.time()

        with self._lock:
            return self._refill(key, current_time)


class RateLimiter:
    """Main rate limiter service."""

    def __init__(self):
        self._configs: Dict[str, RateLimitConfig] = {}
        self._sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self._token_buckets: Dict[str, TokenBucket] = {}
        self._penalties: Dict[str, datetime] = {}
        self._lock = threading.Lock()
        self._initialize_default_limits()

    def _initialize_default_limits(self) -> None:
        """Initialize default rate limits."""
        self.add_config(RateLimitConfig(
            name="global",
            requests=1000,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        ))

        self.add_config(RateLimitConfig(
            name="auth",
            requests=10,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            penalty_seconds=300,
        ))

        self.add_config(RateLimitConfig(
            name="api",
            requests=100,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        ))

        self.add_config(RateLimitConfig(
            name="export",
            requests=10,
            window_seconds=3600,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        ))

    def add_config(self, config: RateLimitConfig) -> None:
        """Add a rate limit configuration."""
        self._configs[config.name] = config

        if config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            self._sliding_windows[config.name] = SlidingWindowCounter(
                config.window_seconds,
                config.requests,
            )
        elif config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            refill_rate = config.requests / config.window_seconds
            capacity = config.burst_size or config.requests
            self._token_buckets[config.name] = TokenBucket(capacity, refill_rate)

    def remove_config(self, name: str) -> bool:
        """Remove a rate limit configuration."""
        if name in self._configs:
            del self._configs[name]
            if name in self._sliding_windows:
                del self._sliding_windows[name]
            if name in self._token_buckets:
                del self._token_buckets[name]
            return True
        return False

    def get_config(self, name: str) -> Optional[RateLimitConfig]:
        """Get a rate limit configuration."""
        return self._configs.get(name)

    def _get_key(
        self,
        config: RateLimitConfig,
        identifier: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> str:
        """Generate a key for the rate limiter."""
        if config.group_by == "user" and user_id:
            return f"{config.name}:user:{user_id}"
        if config.group_by == "organization" and organization_id:
            return f"{config.name}:org:{organization_id}"
        return f"{config.name}:ip:{identifier}"

    def _check_penalty(self, key: str) -> Optional[int]:
        """Check if key is under penalty."""
        with self._lock:
            if key in self._penalties:
                if datetime.utcnow() < self._penalties[key]:
                    remaining = (self._penalties[key] - datetime.utcnow()).seconds
                    return remaining
                del self._penalties[key]
        return None

    def _apply_penalty(self, key: str, seconds: int) -> None:
        """Apply a penalty to a key."""
        with self._lock:
            self._penalties[key] = datetime.utcnow() + timedelta(seconds=seconds)

    def check(
        self,
        rule_name: str,
        identifier: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        path: Optional[str] = None,
        is_authenticated: bool = False,
        consume: bool = True,
    ) -> RateLimitResult:
        """Check if request is within rate limits."""
        config = self._configs.get(rule_name)
        if not config:
            return RateLimitResult(
                allowed=True,
                limit=0,
                remaining=0,
                reset_at=datetime.utcnow(),
            )

        if path and any(path.startswith(p) for p in config.exclude_paths):
            return RateLimitResult(
                allowed=True,
                limit=config.requests,
                remaining=config.requests,
                reset_at=datetime.utcnow() + timedelta(seconds=config.window_seconds),
            )

        if config.apply_to_authenticated_only and not is_authenticated:
            return RateLimitResult(
                allowed=True,
                limit=config.requests,
                remaining=config.requests,
                reset_at=datetime.utcnow() + timedelta(seconds=config.window_seconds),
            )

        if config.apply_to_anonymous_only and is_authenticated:
            return RateLimitResult(
                allowed=True,
                limit=config.requests,
                remaining=config.requests,
                reset_at=datetime.utcnow() + timedelta(seconds=config.window_seconds),
            )

        key = self._get_key(config, identifier, user_id, organization_id)

        penalty_remaining = self._check_penalty(key)
        if penalty_remaining:
            return RateLimitResult(
                allowed=False,
                limit=config.requests,
                remaining=0,
                reset_at=self._penalties[key],
                retry_after_seconds=penalty_remaining,
                rule_name=rule_name,
            )

        if config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            window = self._sliding_windows[rule_name]
            if consume:
                allowed, count, remaining = window.increment(key)
            else:
                count = window.get_count(key)
                remaining = config.requests - count
                allowed = remaining > 0
            reset_at = window.get_reset_time(key)

        elif config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            bucket = self._token_buckets[rule_name]
            if consume:
                allowed, remaining = bucket.consume(key)
            else:
                remaining = bucket.get_tokens(key)
                allowed = remaining >= 1
            remaining = int(remaining)
            reset_at = datetime.utcnow() + timedelta(seconds=1 / (config.requests / config.window_seconds))

        else:
            return RateLimitResult(
                allowed=True,
                limit=config.requests,
                remaining=config.requests,
                reset_at=datetime.utcnow() + timedelta(seconds=config.window_seconds),
            )

        if not allowed and config.penalty_seconds > 0:
            self._apply_penalty(key, config.penalty_seconds)
            return RateLimitResult(
                allowed=False,
                limit=config.requests,
                remaining=0,
                reset_at=datetime.utcnow() + timedelta(seconds=config.penalty_seconds),
                retry_after_seconds=config.penalty_seconds,
                rule_name=rule_name,
            )

        return RateLimitResult(
            allowed=allowed,
            limit=config.requests,
            remaining=remaining,
            reset_at=reset_at,
            retry_after_seconds=None if allowed else config.window_seconds,
            rule_name=rule_name,
        )

    def check_multiple(
        self,
        rules: List[str],
        identifier: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        path: Optional[str] = None,
        is_authenticated: bool = False,
    ) -> RateLimitResult:
        """Check multiple rate limits and return the most restrictive result."""
        most_restrictive = None

        for rule_name in rules:
            result = self.check(
                rule_name=rule_name,
                identifier=identifier,
                user_id=user_id,
                organization_id=organization_id,
                path=path,
                is_authenticated=is_authenticated,
                consume=False,
            )

            if not result.allowed:
                return result

            if most_restrictive is None or result.remaining < most_restrictive.remaining:
                most_restrictive = result

        if most_restrictive:
            for rule_name in rules:
                self.check(
                    rule_name=rule_name,
                    identifier=identifier,
                    user_id=user_id,
                    organization_id=organization_id,
                    consume=True,
                )

        return most_restrictive or RateLimitResult(
            allowed=True,
            limit=0,
            remaining=0,
            reset_at=datetime.utcnow(),
        )

    def reset(self, rule_name: str, identifier: str) -> bool:
        """Reset rate limit for a specific identifier."""
        config = self._configs.get(rule_name)
        if not config:
            return False

        key = f"{rule_name}:ip:{identifier}"

        if rule_name in self._sliding_windows:
            self._sliding_windows[rule_name].reset(key)

        with self._lock:
            if key in self._penalties:
                del self._penalties[key]

        return True

    def get_status(
        self,
        rule_name: str,
        identifier: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get current rate limit status without consuming."""
        result = self.check(
            rule_name=rule_name,
            identifier=identifier,
            user_id=user_id,
            organization_id=organization_id,
            consume=False,
        )

        return {
            "rule": rule_name,
            "limit": result.limit,
            "remaining": result.remaining,
            "reset_at": result.reset_at.isoformat(),
            "is_limited": not result.allowed,
        }


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter) -> None:
    """Set the global rate limiter instance."""
    global _rate_limiter
    _rate_limiter = limiter


def check_rate_limit(
    rule_name: str,
    identifier: str,
    user_id: Optional[str] = None,
) -> RateLimitResult:
    """Check rate limit using the global limiter."""
    return get_rate_limiter().check(rule_name, identifier, user_id)
