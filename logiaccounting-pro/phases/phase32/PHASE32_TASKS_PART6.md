# Phase 32: Advanced Security - Part 6: Rate Limiting & IP Security

## Overview
This part covers rate limiting, IP filtering, and protection against brute force attacks.

---

## File 1: Rate Limiter
**Path:** `backend/app/security/protection/rate_limiter.py`

```python
"""
Rate Limiter
Request rate limiting with sliding window
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time
import logging
from collections import defaultdict
from threading import Lock

from app.security.config import get_security_config

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Rate limit types."""
    IP = "ip"
    USER = "user"
    ENDPOINT = "endpoint"
    GLOBAL = "global"


@dataclass
class RateLimitRule:
    """Rate limit rule definition."""
    name: str
    limit: int  # Max requests
    window_seconds: int  # Time window
    limit_type: RateLimitType = RateLimitType.IP
    burst_limit: Optional[int] = None  # Allow burst
    block_duration_seconds: int = 60  # Block duration when exceeded


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None
    blocked: bool = False
    
    def to_headers(self) -> Dict[str, str]:
        """Convert to rate limit headers."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_at.timestamp())),
        }
        if self.retry_after:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class SlidingWindowCounter:
    """Sliding window rate limit counter."""
    
    def __init__(self):
        self._windows: Dict[str, Dict[int, int]] = defaultdict(dict)
        self._lock = Lock()
    
    def increment(self, key: str, window_seconds: int) -> Tuple[int, int]:
        """
        Increment counter and return (current_count, window_start).
        Uses sliding window algorithm for accurate counting.
        """
        now = int(time.time())
        window_start = now - (now % window_seconds)
        
        with self._lock:
            # Clean old windows
            if key in self._windows:
                self._windows[key] = {
                    ts: count for ts, count in self._windows[key].items()
                    if ts >= window_start - window_seconds
                }
            
            # Increment current window
            if window_start not in self._windows[key]:
                self._windows[key][window_start] = 0
            self._windows[key][window_start] += 1
            
            # Calculate sliding window count
            total = 0
            for ts, count in self._windows[key].items():
                if ts >= window_start - window_seconds:
                    # Weight by overlap with current window
                    if ts == window_start:
                        total += count
                    else:
                        overlap = (ts + window_seconds - window_start) / window_seconds
                        total += int(count * overlap)
            
            return total, window_start
    
    def get_count(self, key: str, window_seconds: int) -> int:
        """Get current count for key."""
        now = int(time.time())
        window_start = now - (now % window_seconds)
        
        with self._lock:
            if key not in self._windows:
                return 0
            
            total = 0
            for ts, count in self._windows[key].items():
                if ts >= window_start - window_seconds:
                    if ts == window_start:
                        total += count
                    else:
                        overlap = (ts + window_seconds - window_start) / window_seconds
                        total += int(count * overlap)
            
            return total
    
    def reset(self, key: str):
        """Reset counter for key."""
        with self._lock:
            if key in self._windows:
                del self._windows[key]


class RateLimiter:
    """Rate limiter service."""
    
    # Default rules
    DEFAULT_RULES = {
        "default": RateLimitRule(
            name="default",
            limit=100,
            window_seconds=60,
        ),
        "login": RateLimitRule(
            name="login",
            limit=5,
            window_seconds=60,
            block_duration_seconds=300,  # 5 min block
        ),
        "password_reset": RateLimitRule(
            name="password_reset",
            limit=3,
            window_seconds=3600,  # 1 hour
            block_duration_seconds=3600,
        ),
        "api": RateLimitRule(
            name="api",
            limit=1000,
            window_seconds=3600,  # 1000/hour
            limit_type=RateLimitType.USER,
        ),
        "export": RateLimitRule(
            name="export",
            limit=10,
            window_seconds=3600,
            limit_type=RateLimitType.USER,
        ),
    }
    
    def __init__(self):
        self.config = get_security_config().rate_limit_policy
        self._counter = SlidingWindowCounter()
        self._blocked: Dict[str, datetime] = {}
        self._rules: Dict[str, RateLimitRule] = self.DEFAULT_RULES.copy()
    
    def check(
        self,
        key: str,
        rule_name: str = "default",
    ) -> RateLimitResult:
        """Check if request is allowed."""
        rule = self._rules.get(rule_name, self._rules["default"])
        
        # Check if blocked
        if key in self._blocked:
            if datetime.utcnow() < self._blocked[key]:
                block_remaining = (self._blocked[key] - datetime.utcnow()).seconds
                return RateLimitResult(
                    allowed=False,
                    limit=rule.limit,
                    remaining=0,
                    reset_at=self._blocked[key],
                    retry_after=block_remaining,
                    blocked=True,
                )
            else:
                del self._blocked[key]
        
        # Increment and check
        count, window_start = self._counter.increment(key, rule.window_seconds)
        reset_at = datetime.fromtimestamp(window_start + rule.window_seconds)
        
        # Check burst limit first
        effective_limit = rule.burst_limit or rule.limit
        
        if count > effective_limit:
            # Block if exceeded
            self._blocked[key] = datetime.utcnow() + timedelta(seconds=rule.block_duration_seconds)
            
            logger.warning(f"Rate limit exceeded for {key} on rule {rule_name}")
            
            return RateLimitResult(
                allowed=False,
                limit=rule.limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=rule.block_duration_seconds,
            )
        
        return RateLimitResult(
            allowed=True,
            limit=rule.limit,
            remaining=rule.limit - count,
            reset_at=reset_at,
        )
    
    def check_and_increment(
        self,
        ip: str = None,
        user_id: str = None,
        endpoint: str = None,
        rule_name: str = "default",
    ) -> RateLimitResult:
        """Check rate limit with automatic key generation."""
        rule = self._rules.get(rule_name, self._rules["default"])
        
        # Build key based on rule type
        if rule.limit_type == RateLimitType.IP:
            key = f"ip:{ip}:{rule_name}"
        elif rule.limit_type == RateLimitType.USER:
            key = f"user:{user_id}:{rule_name}"
        elif rule.limit_type == RateLimitType.ENDPOINT:
            key = f"endpoint:{endpoint}:{ip}"
        else:
            key = f"global:{rule_name}"
        
        return self.check(key, rule_name)
    
    def add_rule(self, rule: RateLimitRule):
        """Add custom rate limit rule."""
        self._rules[rule.name] = rule
    
    def reset(self, key: str):
        """Reset rate limit for key."""
        self._counter.reset(key)
        if key in self._blocked:
            del self._blocked[key]
    
    def unblock(self, key: str):
        """Unblock a key."""
        if key in self._blocked:
            del self._blocked[key]
            logger.info(f"Unblocked: {key}")


# Global rate limiter
rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    return rate_limiter
```

---

## File 2: IP Filter
**Path:** `backend/app/security/protection/ip_filter.py`

```python
"""
IP Filter
IP allowlist/blocklist and geo-filtering
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import ipaddress
import logging

from app.security.config import get_security_config

logger = logging.getLogger(__name__)


class IPRuleType(str, Enum):
    """IP rule types."""
    ALLOW = "allow"
    BLOCK = "block"


@dataclass
class IPRule:
    """IP rule definition."""
    id: str
    ip_or_network: str  # IP or CIDR
    rule_type: IPRuleType
    reason: str = ""
    customer_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def matches(self, ip: str) -> bool:
        """Check if IP matches this rule."""
        try:
            check_ip = ipaddress.ip_address(ip)
            
            if "/" in self.ip_or_network:
                network = ipaddress.ip_network(self.ip_or_network, strict=False)
                return check_ip in network
            else:
                rule_ip = ipaddress.ip_address(self.ip_or_network)
                return check_ip == rule_ip
        except ValueError:
            return False


@dataclass
class IPCheckResult:
    """Result of IP check."""
    allowed: bool
    matched_rule: Optional[IPRule] = None
    reason: str = ""


class IPFilter:
    """IP filtering service."""
    
    # Known bad IP ranges (examples - use threat intelligence in production)
    KNOWN_BAD_RANGES = [
        # Add known malicious ranges here
    ]
    
    def __init__(self):
        self.config = get_security_config()
        self._rules: Dict[str, IPRule] = {}
        self._customer_rules: Dict[str, List[str]] = {}  # customer_id -> [rule_ids]
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize default rules from config."""
        # Add configured allowlist
        for ip in self.config.ip_whitelist:
            self.add_rule(IPRule(
                id=f"config_allow_{ip}",
                ip_or_network=ip,
                rule_type=IPRuleType.ALLOW,
                reason="Configuration allowlist",
            ))
        
        # Add configured blocklist
        for ip in self.config.ip_blacklist:
            self.add_rule(IPRule(
                id=f"config_block_{ip}",
                ip_or_network=ip,
                rule_type=IPRuleType.BLOCK,
                reason="Configuration blocklist",
            ))
    
    def add_rule(self, rule: IPRule) -> IPRule:
        """Add IP rule."""
        self._rules[rule.id] = rule
        
        if rule.customer_id:
            if rule.customer_id not in self._customer_rules:
                self._customer_rules[rule.customer_id] = []
            self._customer_rules[rule.customer_id].append(rule.id)
        
        logger.info(f"IP rule added: {rule.rule_type.value} {rule.ip_or_network}")
        return rule
    
    def remove_rule(self, rule_id: str):
        """Remove IP rule."""
        rule = self._rules.pop(rule_id, None)
        if rule and rule.customer_id:
            if rule.customer_id in self._customer_rules:
                self._customer_rules[rule.customer_id].remove(rule_id)
    
    def check_ip(self, ip: str, customer_id: str = None) -> IPCheckResult:
        """Check if IP is allowed."""
        # Get applicable rules
        applicable_rules = []
        
        # Global rules
        for rule in self._rules.values():
            if not rule.customer_id and not rule.is_expired():
                applicable_rules.append(rule)
        
        # Customer-specific rules
        if customer_id and customer_id in self._customer_rules:
            for rule_id in self._customer_rules[customer_id]:
                rule = self._rules.get(rule_id)
                if rule and not rule.is_expired():
                    applicable_rules.append(rule)
        
        # Check blocklist first (deny takes precedence)
        for rule in applicable_rules:
            if rule.rule_type == IPRuleType.BLOCK and rule.matches(ip):
                logger.warning(f"IP blocked: {ip} (rule: {rule.id})")
                return IPCheckResult(
                    allowed=False,
                    matched_rule=rule,
                    reason=rule.reason or "IP blocked",
                )
        
        # Check if allowlist-only mode
        allow_rules = [r for r in applicable_rules if r.rule_type == IPRuleType.ALLOW]
        
        if allow_rules:
            # If there are allow rules, IP must match one
            for rule in allow_rules:
                if rule.matches(ip):
                    return IPCheckResult(
                        allowed=True,
                        matched_rule=rule,
                    )
            
            # No matching allow rule
            return IPCheckResult(
                allowed=False,
                reason="IP not in allowlist",
            )
        
        # No restrictions - allow by default
        return IPCheckResult(allowed=True)
    
    def block_ip(
        self,
        ip: str,
        reason: str = "",
        duration_hours: int = None,
        customer_id: str = None,
        blocked_by: str = None,
    ) -> IPRule:
        """Block an IP address."""
        from uuid import uuid4
        
        expires_at = None
        if duration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        rule = IPRule(
            id=f"block_{uuid4().hex[:8]}",
            ip_or_network=ip,
            rule_type=IPRuleType.BLOCK,
            reason=reason,
            customer_id=customer_id,
            expires_at=expires_at,
            created_by=blocked_by,
        )
        
        return self.add_rule(rule)
    
    def allow_ip(
        self,
        ip: str,
        reason: str = "",
        customer_id: str = None,
        created_by: str = None,
    ) -> IPRule:
        """Add IP to allowlist."""
        from uuid import uuid4
        
        rule = IPRule(
            id=f"allow_{uuid4().hex[:8]}",
            ip_or_network=ip,
            rule_type=IPRuleType.ALLOW,
            reason=reason,
            customer_id=customer_id,
            created_by=created_by,
        )
        
        return self.add_rule(rule)
    
    def get_rules(
        self,
        customer_id: str = None,
        rule_type: IPRuleType = None,
    ) -> List[IPRule]:
        """Get IP rules."""
        rules = list(self._rules.values())
        
        if customer_id:
            rules = [r for r in rules if r.customer_id == customer_id or not r.customer_id]
        
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        
        return rules
    
    def is_private_ip(self, ip: str) -> bool:
        """Check if IP is private/internal."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False


# Global IP filter
ip_filter = IPFilter()


def get_ip_filter() -> IPFilter:
    """Get IP filter instance."""
    return ip_filter
```

---

## File 3: Input Sanitizer
**Path:** `backend/app/security/protection/sanitizer.py`

```python
"""
Input Sanitizer
Input validation and sanitization
"""

from typing import Any, Dict, List, Optional, Pattern
import re
import html
import logging

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitize and validate user input."""
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
        r"(--|\#|\/\*)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
        r"\.%2e/",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r"`[^`]+`",
    ]
    
    def __init__(self):
        self._sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self._xss_patterns = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.XSS_PATTERNS]
        self._path_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
        self._cmd_patterns = [re.compile(p) for p in self.COMMAND_INJECTION_PATTERNS]
    
    def sanitize_string(self, value: str, allow_html: bool = False) -> str:
        """Sanitize a string value."""
        if not value:
            return value
        
        # Strip leading/trailing whitespace
        value = value.strip()
        
        # HTML escape if not allowed
        if not allow_html:
            value = html.escape(value)
        
        # Remove null bytes
        value = value.replace("\x00", "")
        
        return value
    
    def sanitize_dict(self, data: Dict, allow_html_fields: List[str] = None) -> Dict:
        """Sanitize all string values in a dictionary."""
        allow_html = allow_html_fields or []
        result = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.sanitize_string(value, allow_html=key in allow_html)
            elif isinstance(value, dict):
                result[key] = self.sanitize_dict(value, allow_html)
            elif isinstance(value, list):
                result[key] = self.sanitize_list(value, allow_html)
            else:
                result[key] = value
        
        return result
    
    def sanitize_list(self, data: List, allow_html_fields: List[str] = None) -> List:
        """Sanitize list values."""
        allow_html = allow_html_fields or []
        result = []
        
        for item in data:
            if isinstance(item, str):
                result.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                result.append(self.sanitize_dict(item, allow_html))
            elif isinstance(item, list):
                result.append(self.sanitize_list(item, allow_html))
            else:
                result.append(item)
        
        return result
    
    def check_sql_injection(self, value: str) -> bool:
        """Check for SQL injection patterns."""
        for pattern in self._sql_patterns:
            if pattern.search(value):
                logger.warning(f"SQL injection pattern detected: {value[:100]}")
                return True
        return False
    
    def check_xss(self, value: str) -> bool:
        """Check for XSS patterns."""
        for pattern in self._xss_patterns:
            if pattern.search(value):
                logger.warning(f"XSS pattern detected: {value[:100]}")
                return True
        return False
    
    def check_path_traversal(self, value: str) -> bool:
        """Check for path traversal patterns."""
        for pattern in self._path_patterns:
            if pattern.search(value):
                logger.warning(f"Path traversal pattern detected: {value[:100]}")
                return True
        return False
    
    def check_command_injection(self, value: str) -> bool:
        """Check for command injection patterns."""
        for pattern in self._cmd_patterns:
            if pattern.search(value):
                logger.warning(f"Command injection pattern detected: {value[:100]}")
                return True
        return False
    
    def validate_input(self, value: str) -> Dict[str, Any]:
        """Validate input for security issues."""
        issues = []
        
        if self.check_sql_injection(value):
            issues.append("sql_injection")
        if self.check_xss(value):
            issues.append("xss")
        if self.check_path_traversal(value):
            issues.append("path_traversal")
        if self.check_command_injection(value):
            issues.append("command_injection")
        
        return {
            "safe": len(issues) == 0,
            "issues": issues,
        }
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename."""
        # Remove path separators
        filename = filename.replace("/", "").replace("\\", "")
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', "", filename)
        
        # Remove leading dots (hidden files)
        filename = filename.lstrip(".")
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = name[:250] + ("." + ext if ext else "")
        
        return filename or "unnamed"
    
    def sanitize_email(self, email: str) -> str:
        """Sanitize an email address."""
        # Basic cleanup
        email = email.strip().lower()
        
        # Remove any HTML
        email = html.escape(email)
        
        return email
    
    def sanitize_phone(self, phone: str) -> str:
        """Sanitize a phone number."""
        # Keep only digits and + for international prefix
        return re.sub(r"[^\d+]", "", phone)
    
    def sanitize_url(self, url: str) -> Optional[str]:
        """Sanitize a URL."""
        from urllib.parse import urlparse, urlunparse
        
        try:
            parsed = urlparse(url)
            
            # Only allow http and https
            if parsed.scheme not in ["http", "https"]:
                return None
            
            # Rebuild URL
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                "",
                parsed.query,
                "",
            ))
        except Exception:
            return None


# Global sanitizer
input_sanitizer = InputSanitizer()


def get_input_sanitizer() -> InputSanitizer:
    """Get input sanitizer instance."""
    return input_sanitizer
```

---

## File 4: Protection Module Init
**Path:** `backend/app/security/protection/__init__.py`

```python
"""
Protection Module
Rate limiting, IP filtering, and input sanitization
"""

from app.security.protection.rate_limiter import (
    RateLimiter,
    RateLimitRule,
    RateLimitResult,
    RateLimitType,
    SlidingWindowCounter,
    rate_limiter,
    get_rate_limiter,
)

from app.security.protection.ip_filter import (
    IPFilter,
    IPRule,
    IPRuleType,
    IPCheckResult,
    ip_filter,
    get_ip_filter,
)

from app.security.protection.sanitizer import (
    InputSanitizer,
    input_sanitizer,
    get_input_sanitizer,
)


__all__ = [
    # Rate Limiter
    'RateLimiter',
    'RateLimitRule',
    'RateLimitResult',
    'RateLimitType',
    'SlidingWindowCounter',
    'rate_limiter',
    'get_rate_limiter',
    
    # IP Filter
    'IPFilter',
    'IPRule',
    'IPRuleType',
    'IPCheckResult',
    'ip_filter',
    'get_ip_filter',
    
    # Sanitizer
    'InputSanitizer',
    'input_sanitizer',
    'get_input_sanitizer',
]
```

---

## Summary Part 6

| File | Description | Lines |
|------|-------------|-------|
| `protection/rate_limiter.py` | Rate limiting | ~250 |
| `protection/ip_filter.py` | IP filtering | ~230 |
| `protection/sanitizer.py` | Input sanitization | ~220 |
| `protection/__init__.py` | Protection module exports | ~50 |
| **Total** | | **~750 lines** |
