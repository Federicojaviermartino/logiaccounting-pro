"""
Gateway Data Store
API Keys, Rate Limits, Request Logs for Phase 17
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
from typing import Optional, List, Dict, Any
from uuid import uuid4
import hashlib
import secrets
from collections import defaultdict


class APIKeyStore:
    """Store for API keys with enhanced features"""

    def __init__(self):
        self._keys: Dict[str, dict] = {}
        self._key_hash_index: Dict[str, str] = {}  # hash -> key_id

    def create(self, data: Dict) -> Dict:
        """Create a new API key"""
        key_id = str(uuid4())

        # Generate key
        raw_key = f"la_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]

        key_data = {
            "id": key_id,
            "tenant_id": data.get("tenant_id"),
            "name": data.get("name"),
            "description": data.get("description"),
            "key_prefix": key_prefix,
            "key_hash": key_hash,
            "scopes": data.get("scopes", ["invoices:read", "customers:read"]),
            "environment": data.get("environment", "production"),
            "rate_limit_per_minute": data.get("rate_limit_per_minute"),
            "rate_limit_per_hour": data.get("rate_limit_per_hour"),
            "rate_limit_per_day": data.get("rate_limit_per_day"),
            "allowed_ips": data.get("allowed_ips", []),
            "is_active": True,
            "last_used_at": None,
            "total_requests": 0,
            "expires_at": data.get("expires_at"),
            "created_by": data.get("created_by"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        self._keys[key_id] = key_data
        self._key_hash_index[key_hash] = key_id

        return {**key_data, "raw_key": raw_key}

    def find_by_id(self, key_id: str) -> Optional[Dict]:
        """Find key by ID"""
        return self._keys.get(key_id)

    def find_by_hash(self, key_hash: str) -> Optional[Dict]:
        """Find key by hash"""
        key_id = self._key_hash_index.get(key_hash)
        if key_id:
            return self._keys.get(key_id)
        return None

    def find_by_raw_key(self, raw_key: str) -> Optional[Dict]:
        """Find key by raw key value"""
        if not raw_key or not raw_key.startswith("la_"):
            return None
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return self.find_by_hash(key_hash)

    def find_by_tenant(self, tenant_id: str) -> List[Dict]:
        """Find all keys for a tenant"""
        return [
            k for k in self._keys.values()
            if k.get("tenant_id") == tenant_id
        ]

    def find_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Find all keys with optional filters"""
        results = list(self._keys.values())

        if filters:
            if filters.get("tenant_id"):
                results = [k for k in results if k.get("tenant_id") == filters["tenant_id"]]
            if filters.get("is_active") is not None:
                results = [k for k in results if k.get("is_active") == filters["is_active"]]
            if filters.get("environment"):
                results = [k for k in results if k.get("environment") == filters["environment"]]

        return sorted(results, key=lambda x: x["created_at"], reverse=True)

    def update(self, key_id: str, data: Dict) -> Optional[Dict]:
        """Update an API key"""
        if key_id not in self._keys:
            return None

        key = self._keys[key_id]

        for field in ["name", "description", "scopes", "allowed_ips",
                      "rate_limit_per_minute", "rate_limit_per_hour",
                      "rate_limit_per_day", "is_active"]:
            if field in data:
                key[field] = data[field]

        key["updated_at"] = datetime.utcnow().isoformat()
        return key

    def record_usage(self, key_id: str) -> None:
        """Record API key usage"""
        if key_id in self._keys:
            self._keys[key_id]["last_used_at"] = datetime.utcnow().isoformat()
            self._keys[key_id]["total_requests"] = self._keys[key_id].get("total_requests", 0) + 1

    def regenerate(self, key_id: str) -> Optional[Dict]:
        """Regenerate API key value"""
        if key_id not in self._keys:
            return None

        key = self._keys[key_id]

        # Remove old hash from index
        old_hash = key["key_hash"]
        if old_hash in self._key_hash_index:
            del self._key_hash_index[old_hash]

        # Generate new key
        raw_key = f"la_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]

        key["key_prefix"] = key_prefix
        key["key_hash"] = key_hash
        key["total_requests"] = 0
        key["last_used_at"] = None
        key["updated_at"] = datetime.utcnow().isoformat()

        self._key_hash_index[key_hash] = key_id

        return {**key, "raw_key": raw_key}

    def revoke(self, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id in self._keys:
            self._keys[key_id]["is_active"] = False
            self._keys[key_id]["updated_at"] = datetime.utcnow().isoformat()
            return True
        return False

    def delete(self, key_id: str) -> bool:
        """Delete an API key"""
        if key_id in self._keys:
            key = self._keys[key_id]
            if key["key_hash"] in self._key_hash_index:
                del self._key_hash_index[key["key_hash"]]
            del self._keys[key_id]
            return True
        return False


class RequestLogStore:
    """Store for API request logs"""

    def __init__(self):
        self._logs: List[dict] = []
        self._max_logs = 10000

    def create(self, data: Dict) -> Dict:
        """Create a new request log"""
        log = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            "api_key_id": data.get("api_key_id"),
            "method": data.get("method"),
            "path": data.get("path"),
            "query_params": data.get("query_params"),
            "user_agent": data.get("user_agent"),
            "content_type": data.get("content_type"),
            "client_ip": data.get("client_ip"),
            "status_code": data.get("status_code"),
            "response_time_ms": data.get("response_time_ms"),
            "request_size": data.get("request_size"),
            "response_size": data.get("response_size"),
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message"),
            "api_version": data.get("api_version", "v1"),
            "created_at": datetime.utcnow().isoformat()
        }

        self._logs.insert(0, log)

        # Trim logs if too many
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[:self._max_logs]

        return log

    def find_all(self, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """Find logs with optional filters"""
        results = self._logs

        if filters:
            if filters.get("tenant_id"):
                results = [l for l in results if l.get("tenant_id") == filters["tenant_id"]]
            if filters.get("api_key_id"):
                results = [l for l in results if l.get("api_key_id") == filters["api_key_id"]]
            if filters.get("status_code"):
                results = [l for l in results if l.get("status_code") == filters["status_code"]]
            if filters.get("path"):
                results = [l for l in results if filters["path"] in l.get("path", "")]

        return results[:limit]

    def get_stats(self, tenant_id: str = None, api_key_id: str = None, days: int = 30) -> Dict:
        """Get usage statistics"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        logs = self._logs
        if tenant_id:
            logs = [l for l in logs if l.get("tenant_id") == tenant_id]
        if api_key_id:
            logs = [l for l in logs if l.get("api_key_id") == api_key_id]

        logs = [l for l in logs if l.get("created_at", "") >= cutoff]

        # Calculate stats
        total = len(logs)
        errors = len([l for l in logs if l.get("status_code", 200) >= 400])

        # Group by day
        daily_stats = defaultdict(lambda: {"count": 0, "errors": 0, "total_time": 0})
        for log in logs:
            date = log.get("created_at", "")[:10]
            daily_stats[date]["count"] += 1
            if log.get("status_code", 200) >= 400:
                daily_stats[date]["errors"] += 1
            daily_stats[date]["total_time"] += log.get("response_time_ms", 0)

        # Status code distribution
        status_codes = defaultdict(int)
        for log in logs:
            status_codes[log.get("status_code", 0)] += 1

        # Top endpoints
        endpoints = defaultdict(int)
        for log in logs:
            endpoints[log.get("path", "")] += 1

        top_endpoints = sorted(endpoints.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_requests": total,
            "total_errors": errors,
            "error_rate": round(errors / total * 100, 2) if total > 0 else 0,
            "daily_stats": [
                {
                    "date": date,
                    "count": stats["count"],
                    "errors": stats["errors"],
                    "avg_response_time_ms": round(stats["total_time"] / stats["count"], 2) if stats["count"] > 0 else 0
                }
                for date, stats in sorted(daily_stats.items())
            ],
            "status_codes": dict(status_codes),
            "top_endpoints": [{"path": path, "count": count} for path, count in top_endpoints]
        }


class RateLimitStore:
    """Store for rate limit tracking (in-memory, would use Redis in production)"""

    def __init__(self):
        self._counters: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        # Structure: {identifier: {window: [timestamps]}}

    def check_limit(self, identifier: str, limits: Dict[str, int]) -> Dict[str, Any]:
        """
        Check if request is within rate limits

        Args:
            identifier: Key identifier (e.g., "key:uuid" or "ip:1.2.3.4")
            limits: Dict of window -> limit (e.g., {"minute": 100, "hour": 2000})

        Returns:
            Dict with allowed status and limit info
        """
        import time
        now = time.time()

        window_seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }

        results = {}

        for window, limit in limits.items():
            if limit is None or limit <= 0:
                continue

            ws = window_seconds.get(window, 60)
            cutoff = now - ws

            # Clean old entries
            self._counters[identifier][window] = [
                ts for ts in self._counters[identifier][window]
                if ts > cutoff
            ]

            current = len(self._counters[identifier][window])
            remaining = max(0, limit - current)

            results[window] = {
                "limit": limit,
                "remaining": remaining,
                "reset": int(now + ws)
            }

            if current >= limit:
                return {
                    "allowed": False,
                    "window": window,
                    "limit": limit,
                    "remaining": 0,
                    "reset": int(now + ws),
                    "retry_after": ws,
                    "all_limits": results
                }

        return {
            "allowed": True,
            "all_limits": results
        }

    def record_request(self, identifier: str, windows: List[str] = None):
        """Record a request against rate limits"""
        import time
        now = time.time()

        if windows is None:
            windows = ["minute", "hour", "day"]

        for window in windows:
            self._counters[identifier][window].append(now)

    def get_usage(self, identifier: str) -> Dict[str, int]:
        """Get current usage for all windows"""
        import time
        now = time.time()

        window_seconds = {
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }

        usage = {}
        for window, ws in window_seconds.items():
            cutoff = now - ws
            self._counters[identifier][window] = [
                ts for ts in self._counters[identifier][window]
                if ts > cutoff
            ]
            usage[window] = len(self._counters[identifier][window])

        return usage

    def reset(self, identifier: str, window: str = None):
        """Reset rate limit counters"""
        if window:
            self._counters[identifier][window] = []
        else:
            self._counters[identifier] = defaultdict(list)


class IPAccessRuleStore:
    """Store for IP whitelist/blacklist rules"""

    def __init__(self):
        self._rules: List[dict] = []

    def create(self, data: Dict) -> Dict:
        """Create a new IP access rule"""
        rule = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            "api_key_id": data.get("api_key_id"),
            "ip_address": data.get("ip_address"),
            "cidr_mask": data.get("cidr_mask"),
            "rule_type": data.get("rule_type", "allow"),  # 'allow' or 'deny'
            "description": data.get("description"),
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": data.get("expires_at")
        }

        self._rules.append(rule)
        return rule

    def find_by_tenant(self, tenant_id: str) -> List[Dict]:
        """Find rules for a tenant"""
        return [r for r in self._rules if r.get("tenant_id") == tenant_id]

    def find_by_api_key(self, api_key_id: str) -> List[Dict]:
        """Find rules for an API key"""
        return [r for r in self._rules if r.get("api_key_id") == api_key_id]

    def check_ip_access(self, ip: str, tenant_id: str = None, api_key_id: str = None) -> bool:
        """Check if IP is allowed"""
        import ipaddress

        try:
            client_ip = ipaddress.ip_address(ip)
        except ValueError:
            return False

        # Get applicable rules
        rules = [
            r for r in self._rules
            if (r.get("tenant_id") is None or r.get("tenant_id") == tenant_id) and
               (r.get("api_key_id") is None or r.get("api_key_id") == api_key_id)
        ]

        # Check deny rules first
        for rule in rules:
            if rule["rule_type"] == "deny":
                if self._ip_matches(client_ip, rule):
                    return False

        # Check allow rules
        allow_rules = [r for r in rules if r["rule_type"] == "allow"]

        if not allow_rules:
            return True  # No allow rules = allow all

        for rule in allow_rules:
            if self._ip_matches(client_ip, rule):
                return True

        return False  # Has allow rules but IP not in any

    def _ip_matches(self, ip, rule) -> bool:
        """Check if IP matches rule"""
        import ipaddress

        try:
            if rule.get("cidr_mask"):
                network = ipaddress.ip_network(
                    f"{rule['ip_address']}/{rule['cidr_mask']}",
                    strict=False
                )
                return ip in network
            else:
                return ip == ipaddress.ip_address(rule["ip_address"])
        except ValueError:
            return False

    def delete(self, rule_id: str) -> bool:
        """Delete an IP access rule"""
        for i, rule in enumerate(self._rules):
            if rule["id"] == rule_id:
                self._rules.pop(i)
                return True
        return False


class GatewayDatabase:
    """Gateway database container"""

    def __init__(self):
        self.api_keys = APIKeyStore()
        self.request_logs = RequestLogStore()
        self.rate_limits = RateLimitStore()
        self.ip_rules = IPAccessRuleStore()


# Global gateway database instance
gateway_db = GatewayDatabase()


def init_gateway_database():
    """Initialize gateway database (called from main)"""
    logger.info("Gateway database initialized")
