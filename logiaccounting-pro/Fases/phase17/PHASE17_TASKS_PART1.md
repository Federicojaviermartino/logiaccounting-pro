# LogiAccounting Pro - Phase 17 Tasks Part 1

## API GATEWAY CORE

---

## TASK 1: DATABASE MODELS

### 1.1 API Key Model

**File:** `backend/app/gateway/models/api_key.py`

```python
"""
API Key Model
Secure API key management with scopes and rate limits
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid
import hashlib
import secrets


class APIKey(db.Model):
    """API Key model for external API access"""
    
    __tablename__ = 'api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Key Info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Key Value (hashed)
    key_prefix = Column(String(10), nullable=False, index=True)  # First 8 chars
    key_hash = Column(String(255), nullable=False)
    
    # Scopes/Permissions
    scopes = Column(ARRAY(Text), nullable=False, default=[])
    
    # Environment
    environment = Column(String(20), default='production')
    # 'production', 'sandbox', 'development'
    
    # Rate Limits (override tenant defaults)
    rate_limit_per_minute = Column(Integer)
    rate_limit_per_hour = Column(Integer)
    rate_limit_per_day = Column(Integer)
    
    # IP Restrictions
    allowed_ips = Column(ARRAY(Text))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Usage
    last_used_at = Column(db.DateTime)
    total_requests = Column(BigInteger, default=0)
    
    # Expiration
    expires_at = Column(db.DateTime)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', backref='api_keys')
    creator = relationship('User', foreign_keys=[created_by])
    request_logs = relationship('APIRequestLog', back_populates='api_key', cascade='all, delete-orphan')
    
    # Available scopes
    AVAILABLE_SCOPES = [
        'invoices:read', 'invoices:write',
        'inventory:read', 'inventory:write',
        'customers:read', 'customers:write',
        'suppliers:read', 'suppliers:write',
        'projects:read', 'projects:write',
        'payments:read', 'payments:write',
        'reports:read',
        'documents:read', 'documents:write',
        'webhooks:manage',
        '*',  # Full access
    ]
    
    @staticmethod
    def generate_key() -> tuple:
        """Generate a new API key"""
        # Generate 32-byte random key
        raw_key = secrets.token_urlsafe(32)
        
        # Prefix for identification (first 8 chars)
        prefix = raw_key[:8]
        
        # Full key for user (will be shown only once)
        full_key = f"la_{raw_key}"
        
        # Hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        return full_key, prefix, key_hash
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for comparison"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @classmethod
    def find_by_key(cls, key: str) -> Optional['APIKey']:
        """Find API key by raw key value"""
        if not key or not key.startswith('la_'):
            return None
        
        key_hash = cls.hash_key(key)
        
        return cls.query.filter(
            cls.key_hash == key_hash,
            cls.is_active == True
        ).first()
    
    @property
    def is_valid(self) -> bool:
        """Check if key is valid for use"""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    @property
    def is_expired(self) -> bool:
        """Check if key has expired"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.utcnow()
    
    def has_scope(self, scope: str) -> bool:
        """Check if key has specific scope"""
        if '*' in self.scopes:
            return True
        
        if scope in self.scopes:
            return True
        
        # Check for wildcard in scope (e.g., 'invoices:*')
        scope_base = scope.split(':')[0] if ':' in scope else scope
        if f'{scope_base}:*' in self.scopes:
            return True
        
        return False
    
    def check_ip(self, ip: str) -> bool:
        """Check if IP is allowed"""
        if not self.allowed_ips:
            return True  # No restrictions
        
        return ip in self.allowed_ips
    
    def record_usage(self):
        """Record API key usage"""
        self.last_used_at = datetime.utcnow()
        self.total_requests = (self.total_requests or 0) + 1
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get effective rate limits"""
        return {
            'per_minute': self.rate_limit_per_minute or 100,
            'per_hour': self.rate_limit_per_hour or 2000,
            'per_day': self.rate_limit_per_day or 20000,
        }
    
    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'key_prefix': f"la_{self.key_prefix}...",
            'scopes': self.scopes,
            'environment': self.environment,
            'rate_limits': self.get_rate_limits(),
            'allowed_ips': self.allowed_ips,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'total_requests': self.total_requests,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        return data


class APIRequestLog(db.Model):
    """API request log for auditing and analytics"""
    
    __tablename__ = 'api_request_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    api_key_id = Column(UUID(as_uuid=True), db.ForeignKey('api_keys.id'), index=True)
    
    # Request Info
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    query_params = Column(JSONB)
    
    # Headers (selected)
    user_agent = Column(Text)
    content_type = Column(String(100))
    
    # Client
    client_ip = Column(String(45), nullable=False)
    
    # Response
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    
    # Size
    request_size = Column(Integer)
    response_size = Column(Integer)
    
    # Error
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # API Version
    api_version = Column(String(10))
    
    # Timestamp
    created_at = Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    api_key = relationship('APIKey', back_populates='request_logs')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'method': self.method,
            'path': self.path,
            'status_code': self.status_code,
            'response_time_ms': self.response_time_ms,
            'client_ip': self.client_ip,
            'error_code': self.error_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

### 1.2 Rate Limit Configuration

**File:** `backend/app/gateway/models/rate_limit.py`

```python
"""
Rate Limit Configuration Model
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
import uuid


class RateLimitConfig(db.Model):
    """Rate limit configuration"""
    
    __tablename__ = 'rate_limit_configs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Scope
    scope_type = Column(String(20), nullable=False)  # 'global', 'tenant', 'api_key', 'plan'
    scope_id = Column(UUID(as_uuid=True))  # tenant_id, api_key_id, or plan_id
    
    # Limits
    requests_per_second = Column(Integer)
    requests_per_minute = Column(Integer)
    requests_per_hour = Column(Integer)
    requests_per_day = Column(Integer)
    
    # Burst
    burst_size = Column(Integer, default=10)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('scope_type', 'scope_id', name='uq_rate_limit_scope'),
    )
    
    # Default limits by plan
    DEFAULT_LIMITS = {
        'free': {
            'requests_per_minute': 30,
            'requests_per_hour': 500,
            'requests_per_day': 5000,
            'burst_size': 5,
        },
        'standard': {
            'requests_per_minute': 100,
            'requests_per_hour': 2000,
            'requests_per_day': 20000,
            'burst_size': 10,
        },
        'professional': {
            'requests_per_minute': 300,
            'requests_per_hour': 10000,
            'requests_per_day': 100000,
            'burst_size': 20,
        },
        'business': {
            'requests_per_minute': 1000,
            'requests_per_hour': 50000,
            'requests_per_day': 500000,
            'burst_size': 50,
        },
        'enterprise': {
            'requests_per_minute': 5000,
            'requests_per_hour': 200000,
            'requests_per_day': 2000000,
            'burst_size': 100,
        },
    }
    
    @classmethod
    def get_limits_for_plan(cls, plan: str) -> Dict[str, int]:
        """Get default limits for a plan"""
        return cls.DEFAULT_LIMITS.get(plan, cls.DEFAULT_LIMITS['standard'])
    
    @classmethod
    def get_limits_for_scope(cls, scope_type: str, scope_id: str = None) -> Optional['RateLimitConfig']:
        """Get rate limit config for a scope"""
        query = cls.query.filter(
            cls.scope_type == scope_type,
            cls.is_active == True
        )
        
        if scope_id:
            query = query.filter(cls.scope_id == scope_id)
        else:
            query = query.filter(cls.scope_id == None)
        
        return query.first()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'scope_type': self.scope_type,
            'scope_id': str(self.scope_id) if self.scope_id else None,
            'requests_per_second': self.requests_per_second,
            'requests_per_minute': self.requests_per_minute,
            'requests_per_hour': self.requests_per_hour,
            'requests_per_day': self.requests_per_day,
            'burst_size': self.burst_size,
        }


class IPAccessRule(db.Model):
    """IP whitelist/blacklist rules"""
    
    __tablename__ = 'ip_access_rules'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'))
    api_key_id = Column(UUID(as_uuid=True), db.ForeignKey('api_keys.id', ondelete='CASCADE'))
    
    # Rule
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    cidr_mask = Column(Integer)  # For IP ranges
    
    # Type
    rule_type = Column(String(10), nullable=False)  # 'allow', 'deny'
    
    # Scope
    scope = Column(String(20), default='all')  # 'all', 'api_key', 'tenant'
    
    # Metadata
    description = Column(String(255))
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    expires_at = Column(db.DateTime)
    
    @classmethod
    def check_ip_access(cls, ip: str, tenant_id: str = None, api_key_id: str = None) -> bool:
        """Check if IP is allowed"""
        import ipaddress
        
        try:
            client_ip = ipaddress.ip_address(ip)
        except ValueError:
            return False
        
        # Get applicable rules
        query = cls.query.filter(
            db.or_(
                cls.tenant_id == None,
                cls.tenant_id == tenant_id
            ),
            db.or_(
                cls.api_key_id == None,
                cls.api_key_id == api_key_id
            )
        )
        
        rules = query.all()
        
        # Check deny rules first
        for rule in rules:
            if rule.rule_type == 'deny':
                if cls._ip_matches(client_ip, rule):
                    return False
        
        # Check if there are allow rules
        allow_rules = [r for r in rules if r.rule_type == 'allow']
        
        if not allow_rules:
            return True  # No allow rules = allow all
        
        # Check allow rules
        for rule in allow_rules:
            if cls._ip_matches(client_ip, rule):
                return True
        
        return False  # Has allow rules but IP not in any
    
    @staticmethod
    def _ip_matches(ip, rule) -> bool:
        """Check if IP matches rule"""
        import ipaddress
        
        try:
            if rule.cidr_mask:
                network = ipaddress.ip_network(f"{rule.ip_address}/{rule.cidr_mask}", strict=False)
                return ip in network
            else:
                return ip == ipaddress.ip_address(rule.ip_address)
        except ValueError:
            return False
```

---

## TASK 2: API KEY AUTHENTICATION

### 2.1 API Key Auth Handler

**File:** `backend/app/gateway/core/api_key_auth.py`

```python
"""
API Key Authentication
Authenticate requests using API keys
"""

from flask import request, g, jsonify
from functools import wraps
from typing import Optional, Callable, List
import logging

from app.gateway.models.api_key import APIKey
from app.tenancy.core.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class APIKeyAuth:
    """API Key authentication handler"""
    
    HEADER_NAME = 'X-API-Key'
    BEARER_PREFIX = 'Bearer '
    
    @classmethod
    def extract_api_key(cls) -> Optional[str]:
        """Extract API key from request"""
        # Check header
        api_key = request.headers.get(cls.HEADER_NAME)
        if api_key:
            return api_key
        
        # Check Authorization header with Bearer prefix
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith(cls.BEARER_PREFIX):
            return auth_header[len(cls.BEARER_PREFIX):]
        
        # Check query parameter (for webhooks, etc.)
        api_key = request.args.get('api_key')
        if api_key:
            return api_key
        
        return None
    
    @classmethod
    def authenticate(cls) -> tuple:
        """
        Authenticate request using API key
        
        Returns:
            Tuple of (api_key, tenant, error_response)
        """
        raw_key = cls.extract_api_key()
        
        if not raw_key:
            return None, None, {
                'success': False,
                'error': 'API key required',
                'code': 'API_KEY_MISSING'
            }
        
        # Find API key
        api_key = APIKey.find_by_key(raw_key)
        
        if not api_key:
            logger.warning(f"Invalid API key attempt: {raw_key[:12]}...")
            return None, None, {
                'success': False,
                'error': 'Invalid API key',
                'code': 'API_KEY_INVALID'
            }
        
        # Check if valid
        if not api_key.is_valid:
            if api_key.is_expired:
                return None, None, {
                    'success': False,
                    'error': 'API key has expired',
                    'code': 'API_KEY_EXPIRED'
                }
            else:
                return None, None, {
                    'success': False,
                    'error': 'API key is inactive',
                    'code': 'API_KEY_INACTIVE'
                }
        
        # Check IP restriction
        client_ip = cls.get_client_ip()
        if not api_key.check_ip(client_ip):
            logger.warning(f"IP {client_ip} not allowed for API key {api_key.id}")
            return None, None, {
                'success': False,
                'error': 'IP address not allowed',
                'code': 'IP_NOT_ALLOWED'
            }
        
        # Get tenant
        from app.tenancy.services.tenant_service import TenantService
        tenant = TenantService.get_tenant(str(api_key.tenant_id))
        
        if not tenant or not tenant.is_active:
            return None, None, {
                'success': False,
                'error': 'Tenant not found or inactive',
                'code': 'TENANT_INACTIVE'
            }
        
        return api_key, tenant, None
    
    @staticmethod
    def get_client_ip() -> str:
        """Get client IP address"""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr


def require_api_key(f: Callable) -> Callable:
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key, tenant, error = APIKeyAuth.authenticate()
        
        if error:
            return jsonify(error), 401
        
        # Set context
        g.api_key = api_key
        g.tenant = tenant
        TenantContext.set_current_tenant(tenant)
        
        # Record usage
        api_key.record_usage()
        
        return f(*args, **kwargs)
    
    return decorated


def require_scope(scope: str):
    """Decorator to require specific API key scope"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = getattr(g, 'api_key', None)
            
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': 'API key required',
                    'code': 'API_KEY_MISSING'
                }), 401
            
            if not api_key.has_scope(scope):
                return jsonify({
                    'success': False,
                    'error': f'Missing required scope: {scope}',
                    'code': 'INSUFFICIENT_SCOPE'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def require_scopes(scopes: List[str], require_all: bool = True):
    """Decorator to require multiple scopes"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = getattr(g, 'api_key', None)
            
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': 'API key required',
                    'code': 'API_KEY_MISSING'
                }), 401
            
            if require_all:
                # Must have all scopes
                missing = [s for s in scopes if not api_key.has_scope(s)]
                if missing:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required scopes: {", ".join(missing)}',
                        'code': 'INSUFFICIENT_SCOPE'
                    }), 403
            else:
                # Must have at least one scope
                has_any = any(api_key.has_scope(s) for s in scopes)
                if not has_any:
                    return jsonify({
                        'success': False,
                        'error': f'Requires one of: {", ".join(scopes)}',
                        'code': 'INSUFFICIENT_SCOPE'
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator
```

---

## TASK 3: RATE LIMITER

### 3.1 Rate Limiter Implementation

**File:** `backend/app/gateway/core/rate_limiter.py`

```python
"""
Rate Limiter
Redis-based rate limiting with multiple time windows
"""

from flask import request, g, jsonify
from functools import wraps
from typing import Optional, Dict, Any, Callable
import time
import logging
import redis

from app.gateway.models.rate_limit import RateLimitConfig

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter using sliding window"""
    
    def __init__(self, redis_url: str = None):
        self.redis_client = redis.from_url(
            redis_url or 'redis://localhost:6379/1',
            decode_responses=True
        )
    
    def _get_key(self, identifier: str, window: str) -> str:
        """Generate Redis key for rate limit"""
        return f"rate_limit:{identifier}:{window}"
    
    def _get_window_seconds(self, window: str) -> int:
        """Get window duration in seconds"""
        windows = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400,
        }
        return windows.get(window, 60)
    
    def check_rate_limit(
        self,
        identifier: str,
        limits: Dict[str, int],
        burst_size: int = 10
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Args:
            identifier: Unique identifier (api_key_id, tenant_id, IP)
            limits: Dict of window -> limit mappings
            burst_size: Maximum burst allowance
            
        Returns:
            Dict with allowed status and limit info
        """
        now = time.time()
        results = {}
        
        for window, limit in limits.items():
            if limit is None or limit <= 0:
                continue
            
            key = self._get_key(identifier, window)
            window_seconds = self._get_window_seconds(window)
            
            # Use sliding window counter
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            cutoff = now - window_seconds
            pipe.zremrangebyscore(key, 0, cutoff)
            
            # Count current entries
            pipe.zcard(key)
            
            # Execute pipeline
            _, current_count = pipe.execute()
            
            # Check limit
            remaining = max(0, limit - current_count)
            
            results[window] = {
                'limit': limit,
                'remaining': remaining,
                'reset': int(now + window_seconds),
            }
            
            if current_count >= limit:
                return {
                    'allowed': False,
                    'window': window,
                    'limit': limit,
                    'remaining': 0,
                    'reset': int(now + window_seconds),
                    'retry_after': window_seconds,
                    'all_limits': results,
                }
        
        return {
            'allowed': True,
            'all_limits': results,
        }
    
    def record_request(self, identifier: str, windows: list = None):
        """Record a request against rate limits"""
        now = time.time()
        
        if windows is None:
            windows = ['second', 'minute', 'hour', 'day']
        
        pipe = self.redis_client.pipeline()
        
        for window in windows:
            key = self._get_key(identifier, window)
            window_seconds = self._get_window_seconds(window)
            
            # Add entry with current timestamp as score
            pipe.zadd(key, {f"{now}:{id(now)}": now})
            
            # Set expiration (window duration + buffer)
            pipe.expire(key, window_seconds + 60)
        
        pipe.execute()
    
    def get_usage(self, identifier: str) -> Dict[str, int]:
        """Get current usage for all windows"""
        now = time.time()
        usage = {}
        
        for window in ['minute', 'hour', 'day']:
            key = self._get_key(identifier, window)
            window_seconds = self._get_window_seconds(window)
            
            # Remove expired and count
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            pipe.zcard(key)
            _, count = pipe.execute()
            
            usage[window] = count
        
        return usage
    
    def reset(self, identifier: str, window: str = None):
        """Reset rate limit counters"""
        if window:
            key = self._get_key(identifier, window)
            self.redis_client.delete(key)
        else:
            # Reset all windows
            for w in ['second', 'minute', 'hour', 'day']:
                key = self._get_key(identifier, w)
                self.redis_client.delete(key)


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(
    limits: Dict[str, int] = None,
    key_func: Callable = None,
    scope: str = None
):
    """
    Rate limit decorator
    
    Args:
        limits: Custom limits {window: count}
        key_func: Function to generate rate limit key
        scope: Endpoint scope for different limits
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            # Get rate limit identifier
            if key_func:
                identifier = key_func()
            else:
                identifier = _get_default_identifier()
            
            # Get limits
            effective_limits = limits or _get_effective_limits()
            
            # Check rate limit
            result = rate_limiter.check_rate_limit(identifier, effective_limits)
            
            if not result['allowed']:
                # Add rate limit headers
                response = jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'limit': result['limit'],
                    'window': result['window'],
                    'retry_after': result['retry_after'],
                })
                response.status_code = 429
                
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(result['reset'])
                response.headers['Retry-After'] = str(result['retry_after'])
                
                return response
            
            # Record request
            rate_limiter.record_request(identifier)
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Add rate limit headers to successful response
            if hasattr(response, 'headers') and result.get('all_limits'):
                minute_info = result['all_limits'].get('minute', {})
                response.headers['X-RateLimit-Limit'] = str(minute_info.get('limit', 0))
                response.headers['X-RateLimit-Remaining'] = str(minute_info.get('remaining', 0))
                response.headers['X-RateLimit-Reset'] = str(minute_info.get('reset', 0))
            
            return response
        
        return decorated
    return decorator


def _get_default_identifier() -> str:
    """Get default rate limit identifier"""
    # Priority: API key > Tenant > IP
    api_key = getattr(g, 'api_key', None)
    if api_key:
        return f"key:{api_key.id}"
    
    tenant = getattr(g, 'tenant', None)
    if tenant:
        return f"tenant:{tenant.id}"
    
    # Fall back to IP
    return f"ip:{request.remote_addr}"


def _get_effective_limits() -> Dict[str, int]:
    """Get effective rate limits for current request"""
    api_key = getattr(g, 'api_key', None)
    
    if api_key:
        # API key specific limits
        return {
            'minute': api_key.rate_limit_per_minute or 100,
            'hour': api_key.rate_limit_per_hour or 2000,
            'day': api_key.rate_limit_per_day or 20000,
        }
    
    tenant = getattr(g, 'tenant', None)
    if tenant:
        # Get tenant plan limits
        plan_limits = RateLimitConfig.get_limits_for_plan(tenant.tier)
        return {
            'minute': plan_limits.get('requests_per_minute', 100),
            'hour': plan_limits.get('requests_per_hour', 2000),
            'day': plan_limits.get('requests_per_day', 20000),
        }
    
    # Default limits for unauthenticated requests
    return {
        'minute': 30,
        'hour': 500,
        'day': 5000,
    }
```

---

## TASK 4: REQUEST LOGGER

### 4.1 Request/Response Logging

**File:** `backend/app/gateway/core/request_logger.py`

```python
"""
Request Logger
Log API requests and responses for auditing and analytics
"""

from flask import request, g
from functools import wraps
from typing import Optional, Callable
import time
import logging
import json

from app.extensions import db
from app.gateway.models.api_key import APIRequestLog

logger = logging.getLogger(__name__)


class RequestLogger:
    """API request logger"""
    
    # Paths to exclude from logging
    EXCLUDED_PATHS = [
        '/health',
        '/api/v1/docs',
        '/static',
    ]
    
    # Headers to capture
    CAPTURED_HEADERS = [
        'User-Agent',
        'Content-Type',
        'Accept',
        'X-Request-ID',
    ]
    
    # Maximum body size to log (bytes)
    MAX_BODY_LOG_SIZE = 10000
    
    @classmethod
    def should_log(cls, path: str) -> bool:
        """Check if request should be logged"""
        for excluded in cls.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return False
        return True
    
    @classmethod
    def log_request(
        cls,
        response,
        start_time: float,
        error_code: str = None,
        error_message: str = None
    ):
        """Log a completed request"""
        if not cls.should_log(request.path):
            return
        
        try:
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Get tenant and API key from context
            tenant_id = None
            api_key_id = None
            
            if hasattr(g, 'tenant') and g.tenant:
                tenant_id = g.tenant.id
            
            if hasattr(g, 'api_key') and g.api_key:
                api_key_id = g.api_key.id
            
            if not tenant_id:
                # Can't log without tenant context
                return
            
            # Create log entry
            log_entry = APIRequestLog(
                tenant_id=tenant_id,
                api_key_id=api_key_id,
                method=request.method,
                path=request.path,
                query_params=dict(request.args) if request.args else None,
                user_agent=request.headers.get('User-Agent'),
                content_type=request.headers.get('Content-Type'),
                client_ip=cls._get_client_ip(),
                status_code=response.status_code if hasattr(response, 'status_code') else 200,
                response_time_ms=response_time_ms,
                request_size=request.content_length,
                response_size=len(response.get_data()) if hasattr(response, 'get_data') else None,
                error_code=error_code,
                error_message=error_message,
                api_version=cls._extract_api_version(),
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
            db.session.rollback()
    
    @staticmethod
    def _get_client_ip() -> str:
        """Get client IP address"""
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr
    
    @staticmethod
    def _extract_api_version() -> Optional[str]:
        """Extract API version from path"""
        path = request.path
        if '/api/v' in path:
            parts = path.split('/')
            for part in parts:
                if part.startswith('v') and len(part) <= 3:
                    return part
        return 'v1'


def log_api_request(f: Callable) -> Callable:
    """Decorator to log API requests"""
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        error_code = None
        error_message = None
        
        try:
            response = f(*args, **kwargs)
            
            # Check if response indicates error
            if hasattr(response, 'status_code') and response.status_code >= 400:
                try:
                    data = response.get_json()
                    error_code = data.get('code')
                    error_message = data.get('error')
                except:
                    pass
            
            return response
            
        except Exception as e:
            error_code = 'INTERNAL_ERROR'
            error_message = str(e)
            raise
            
        finally:
            # Log request (always, even on error)
            try:
                response_obj = response if 'response' in locals() else None
                RequestLogger.log_request(
                    response_obj,
                    start_time,
                    error_code,
                    error_message
                )
            except:
                pass
    
    return decorated


class RequestLogMiddleware:
    """Middleware for automatic request logging"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
    
    def _before_request(self):
        """Record request start time"""
        g.request_start_time = time.time()
    
    def _after_request(self, response):
        """Log request after completion"""
        start_time = getattr(g, 'request_start_time', time.time())
        
        # Only log API requests
        if request.path.startswith('/api/'):
            RequestLogger.log_request(response, start_time)
        
        return response
```

---

## TASK 5: API KEY SERVICE

### 5.1 API Key Management Service

**File:** `backend/app/gateway/services/api_key_service.py`

```python
"""
API Key Service
Manage API keys for tenants
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from app.extensions import db
from app.gateway.models.api_key import APIKey
from app.tenancy.core.tenant_context import TenantContext
from app.tenancy.services.quota_service import QuotaService

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for API key operations"""
    
    # Default scopes for new keys
    DEFAULT_SCOPES = ['invoices:read', 'customers:read', 'inventory:read']
    
    @staticmethod
    def create_api_key(
        name: str,
        scopes: List[str] = None,
        description: str = None,
        environment: str = 'production',
        expires_in_days: int = None,
        allowed_ips: List[str] = None,
        rate_limit_per_minute: int = None,
        created_by: str = None,
        tenant=None
    ) -> Dict[str, Any]:
        """
        Create a new API key
        
        Returns:
            Dict with api_key object and the raw key (shown only once)
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            raise ValueError("Tenant context required")
        
        # Check quota
        # check = QuotaService.check_quota('api_keys', tenant=tenant)
        # if not check['allowed']:
        #     raise ValueError("API key limit reached")
        
        # Validate scopes
        if scopes:
            invalid_scopes = [s for s in scopes if s not in APIKey.AVAILABLE_SCOPES]
            if invalid_scopes:
                raise ValueError(f"Invalid scopes: {invalid_scopes}")
        else:
            scopes = APIKeyService.DEFAULT_SCOPES
        
        # Generate key
        raw_key, prefix, key_hash = APIKey.generate_key()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key
        api_key = APIKey(
            tenant_id=tenant.id,
            name=name,
            description=description,
            key_prefix=prefix,
            key_hash=key_hash,
            scopes=scopes,
            environment=environment,
            allowed_ips=allowed_ips,
            rate_limit_per_minute=rate_limit_per_minute,
            expires_at=expires_at,
            created_by=created_by,
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        logger.info(f"Created API key: {api_key.id} for tenant {tenant.slug}")
        
        return {
            'api_key': api_key,
            'raw_key': raw_key,  # Only returned once!
        }
    
    @staticmethod
    def get_api_key(key_id: str, tenant=None) -> Optional[APIKey]:
        """Get API key by ID"""
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        return APIKey.query.filter(
            APIKey.id == key_id,
            APIKey.tenant_id == tenant.id
        ).first()
    
    @staticmethod
    def list_api_keys(
        tenant=None,
        is_active: bool = None,
        environment: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> tuple:
        """List API keys for tenant"""
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        query = APIKey.query.filter(APIKey.tenant_id == tenant.id)
        
        if is_active is not None:
            query = query.filter(APIKey.is_active == is_active)
        
        if environment:
            query = query.filter(APIKey.environment == environment)
        
        query = query.order_by(APIKey.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination.items, pagination.total
    
    @staticmethod
    def update_api_key(
        key_id: str,
        name: str = None,
        description: str = None,
        scopes: List[str] = None,
        allowed_ips: List[str] = None,
        rate_limit_per_minute: int = None,
        is_active: bool = None,
        tenant=None
    ) -> Optional[APIKey]:
        """Update API key"""
        api_key = APIKeyService.get_api_key(key_id, tenant)
        
        if not api_key:
            return None
        
        if name is not None:
            api_key.name = name
        
        if description is not None:
            api_key.description = description
        
        if scopes is not None:
            # Validate scopes
            invalid_scopes = [s for s in scopes if s not in APIKey.AVAILABLE_SCOPES]
            if invalid_scopes:
                raise ValueError(f"Invalid scopes: {invalid_scopes}")
            api_key.scopes = scopes
        
        if allowed_ips is not None:
            api_key.allowed_ips = allowed_ips
        
        if rate_limit_per_minute is not None:
            api_key.rate_limit_per_minute = rate_limit_per_minute
        
        if is_active is not None:
            api_key.is_active = is_active
        
        db.session.commit()
        
        logger.info(f"Updated API key: {api_key.id}")
        
        return api_key
    
    @staticmethod
    def regenerate_api_key(key_id: str, tenant=None) -> Dict[str, Any]:
        """Regenerate API key (new key value, same settings)"""
        api_key = APIKeyService.get_api_key(key_id, tenant)
        
        if not api_key:
            return None
        
        # Generate new key
        raw_key, prefix, key_hash = APIKey.generate_key()
        
        api_key.key_prefix = prefix
        api_key.key_hash = key_hash
        api_key.total_requests = 0
        api_key.last_used_at = None
        
        db.session.commit()
        
        logger.info(f"Regenerated API key: {api_key.id}")
        
        return {
            'api_key': api_key,
            'raw_key': raw_key,
        }
    
    @staticmethod
    def revoke_api_key(key_id: str, tenant=None) -> bool:
        """Revoke (deactivate) an API key"""
        api_key = APIKeyService.get_api_key(key_id, tenant)
        
        if not api_key:
            return False
        
        api_key.is_active = False
        db.session.commit()
        
        logger.info(f"Revoked API key: {api_key.id}")
        
        return True
    
    @staticmethod
    def delete_api_key(key_id: str, tenant=None) -> bool:
        """Permanently delete an API key"""
        api_key = APIKeyService.get_api_key(key_id, tenant)
        
        if not api_key:
            return False
        
        db.session.delete(api_key)
        db.session.commit()
        
        logger.info(f"Deleted API key: {api_key.id}")
        
        return True
    
    @staticmethod
    def get_usage_stats(key_id: str, days: int = 30, tenant=None) -> Dict[str, Any]:
        """Get usage statistics for an API key"""
        from sqlalchemy import func
        from app.gateway.models.api_key import APIRequestLog
        
        api_key = APIKeyService.get_api_key(key_id, tenant)
        
        if not api_key:
            return None
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get request counts by day
        daily_stats = db.session.query(
            func.date(APIRequestLog.created_at).label('date'),
            func.count(APIRequestLog.id).label('count'),
            func.avg(APIRequestLog.response_time_ms).label('avg_response_time')
        ).filter(
            APIRequestLog.api_key_id == api_key.id,
            APIRequestLog.created_at >= cutoff
        ).group_by(
            func.date(APIRequestLog.created_at)
        ).all()
        
        # Get status code distribution
        status_stats = db.session.query(
            APIRequestLog.status_code,
            func.count(APIRequestLog.id).label('count')
        ).filter(
            APIRequestLog.api_key_id == api_key.id,
            APIRequestLog.created_at >= cutoff
        ).group_by(
            APIRequestLog.status_code
        ).all()
        
        # Get top endpoints
        endpoint_stats = db.session.query(
            APIRequestLog.path,
            func.count(APIRequestLog.id).label('count')
        ).filter(
            APIRequestLog.api_key_id == api_key.id,
            APIRequestLog.created_at >= cutoff
        ).group_by(
            APIRequestLog.path
        ).order_by(
            func.count(APIRequestLog.id).desc()
        ).limit(10).all()
        
        return {
            'api_key_id': str(api_key.id),
            'period_days': days,
            'total_requests': api_key.total_requests,
            'last_used_at': api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            'daily_stats': [
                {
                    'date': str(row.date),
                    'count': row.count,
                    'avg_response_time_ms': round(row.avg_response_time, 2) if row.avg_response_time else 0
                }
                for row in daily_stats
            ],
            'status_codes': {
                row.status_code: row.count
                for row in status_stats
            },
            'top_endpoints': [
                {'path': row.path, 'count': row.count}
                for row in endpoint_stats
            ],
        }
```

---

## Continue to Part 2 for Webhooks System

---

*Phase 17 Tasks Part 1 - LogiAccounting Pro*
*API Gateway Core*
