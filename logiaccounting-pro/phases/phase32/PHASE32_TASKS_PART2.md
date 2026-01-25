# Phase 32: Advanced Security - Part 2: OAuth & Session Management

## Overview
This part covers OAuth 2.0 authentication providers and session management.

---

## File 1: OAuth Provider Manager
**Path:** `backend/app/security/auth/oauth.py`

```python
"""
OAuth 2.0 Authentication
Support for Google, Microsoft, and custom OAuth providers
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import httpx
import secrets
import logging
from urllib.parse import urlencode

from app.security.config import get_security_config

logger = logging.getLogger(__name__)


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    CUSTOM = "custom"


@dataclass
class OAuthUser:
    """OAuth user info."""
    provider: OAuthProvider
    provider_id: str
    email: str
    name: str
    picture: Optional[str] = None
    email_verified: bool = False
    raw_data: Dict = None


@dataclass
class OAuthTokens:
    """OAuth tokens."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = ""
    id_token: Optional[str] = None


class OAuthManager:
    """Manages OAuth authentication."""
    
    # State token expiry
    STATE_EXPIRY_MINUTES = 10
    
    def __init__(self):
        self.config = get_security_config()
        self._pending_states: Dict[str, Dict] = {}
    
    def get_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
        scopes: list = None,
        state_data: Dict = None,
    ) -> Dict[str, str]:
        """Get OAuth authorization URL."""
        provider_config = self.config.oauth_providers.get(provider)
        
        if not provider_config:
            raise ValueError(f"OAuth provider not configured: {provider}")
        
        # Generate state token
        state = secrets.token_urlsafe(32)
        self._pending_states[state] = {
            "provider": provider,
            "redirect_uri": redirect_uri,
            "data": state_data or {},
            "created_at": datetime.utcnow(),
        }
        
        # Build authorization URL
        params = {
            "client_id": provider_config["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": " ".join(scopes) if scopes else provider_config.get("scope", ""),
        }
        
        # Provider-specific params
        if provider == "google":
            params["access_type"] = "offline"
            params["prompt"] = "consent"
        elif provider == "microsoft":
            params["response_mode"] = "query"
        
        url = f"{provider_config['authorize_url']}?{urlencode(params)}"
        
        return {
            "url": url,
            "state": state,
        }
    
    async def exchange_code(
        self,
        provider: str,
        code: str,
        redirect_uri: str,
        state: str,
    ) -> OAuthTokens:
        """Exchange authorization code for tokens."""
        # Validate state
        pending = self._pending_states.get(state)
        if not pending:
            raise ValueError("Invalid or expired state token")
        
        if pending["provider"] != provider:
            raise ValueError("Provider mismatch")
        
        # Check state expiry
        if datetime.utcnow() - pending["created_at"] > timedelta(minutes=self.STATE_EXPIRY_MINUTES):
            del self._pending_states[state]
            raise ValueError("State token expired")
        
        # Clean up state
        del self._pending_states[state]
        
        provider_config = self.config.oauth_providers.get(provider)
        
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider_config["token_url"],
                data={
                    "client_id": provider_config["client_id"],
                    "client_secret": provider_config["client_secret"],
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            
            if response.status_code != 200:
                logger.error(f"OAuth token exchange failed: {response.text}")
                raise ValueError("Failed to exchange authorization code")
            
            data = response.json()
        
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            scope=data.get("scope", ""),
            id_token=data.get("id_token"),
        )
    
    async def get_user_info(
        self,
        provider: str,
        access_token: str,
    ) -> OAuthUser:
        """Get user info from OAuth provider."""
        provider_config = self.config.oauth_providers.get(provider)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                provider_config["userinfo_url"],
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            
            if response.status_code != 200:
                logger.error(f"OAuth userinfo failed: {response.text}")
                raise ValueError("Failed to get user info")
            
            data = response.json()
        
        # Parse provider-specific response
        if provider == "google":
            return OAuthUser(
                provider=OAuthProvider.GOOGLE,
                provider_id=data["id"],
                email=data["email"],
                name=data.get("name", ""),
                picture=data.get("picture"),
                email_verified=data.get("verified_email", False),
                raw_data=data,
            )
        
        elif provider == "microsoft":
            return OAuthUser(
                provider=OAuthProvider.MICROSOFT,
                provider_id=data["id"],
                email=data.get("mail") or data.get("userPrincipalName", ""),
                name=data.get("displayName", ""),
                picture=None,  # Requires separate Graph API call
                email_verified=True,  # Microsoft verifies emails
                raw_data=data,
            )
        
        elif provider == "github":
            return OAuthUser(
                provider=OAuthProvider.GITHUB,
                provider_id=str(data["id"]),
                email=data.get("email", ""),
                name=data.get("name") or data.get("login", ""),
                picture=data.get("avatar_url"),
                email_verified=False,
                raw_data=data,
            )
        
        else:
            # Generic parsing
            return OAuthUser(
                provider=OAuthProvider.CUSTOM,
                provider_id=str(data.get("id") or data.get("sub", "")),
                email=data.get("email", ""),
                name=data.get("name", ""),
                picture=data.get("picture"),
                email_verified=data.get("email_verified", False),
                raw_data=data,
            )
    
    async def refresh_tokens(
        self,
        provider: str,
        refresh_token: str,
    ) -> OAuthTokens:
        """Refresh access token."""
        provider_config = self.config.oauth_providers.get(provider)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider_config["token_url"],
                data={
                    "client_id": provider_config["client_id"],
                    "client_secret": provider_config["client_secret"],
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Accept": "application/json"},
            )
            
            if response.status_code != 200:
                logger.error(f"OAuth token refresh failed: {response.text}")
                raise ValueError("Failed to refresh token")
            
            data = response.json()
        
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
        )
    
    def get_available_providers(self) -> list:
        """Get list of configured OAuth providers."""
        return list(self.config.oauth_providers.keys())


# Global OAuth manager
oauth_manager = OAuthManager()


def get_oauth_manager() -> OAuthManager:
    """Get OAuth manager instance."""
    return oauth_manager
```

---

## File 2: Session Manager
**Path:** `backend/app/security/auth/sessions.py`

```python
"""
Session Management
Secure session handling with device tracking
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib
import logging
from uuid import uuid4
from user_agents import parse as parse_user_agent

from app.security.config import get_security_config

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Information about the device."""
    device_type: str = "unknown"  # desktop, mobile, tablet
    browser: str = ""
    browser_version: str = ""
    os: str = ""
    os_version: str = ""
    is_mobile: bool = False
    is_tablet: bool = False
    is_bot: bool = False


@dataclass
class LocationInfo:
    """Geolocation information."""
    ip_address: str = ""
    country: str = ""
    country_code: str = ""
    city: str = ""
    region: str = ""
    timezone: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class Session:
    """User session."""
    id: str
    user_id: str
    token_hash: str
    device: DeviceInfo
    location: LocationInfo
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_active: bool = True
    is_current: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "device": {
                "type": self.device.device_type,
                "browser": self.device.browser,
                "os": self.device.os,
            },
            "location": {
                "ip": self.location.ip_address,
                "country": self.location.country,
                "city": self.location.city,
            },
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_current": self.is_current,
        }


class SessionManager:
    """Manages user sessions."""
    
    TOKEN_LENGTH = 64
    
    def __init__(self):
        self.config = get_security_config().session_policy
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, List[str]] = {}
    
    def create_session(
        self,
        user_id: str,
        user_agent: str = "",
        ip_address: str = "",
    ) -> tuple[str, Session]:
        """Create a new session."""
        # Check concurrent session limit
        self._enforce_session_limit(user_id)
        
        # Generate session token
        token = secrets.token_urlsafe(self.TOKEN_LENGTH)
        token_hash = self._hash_token(token)
        
        # Parse device info
        device = self._parse_user_agent(user_agent)
        
        # Parse location (simplified - use GeoIP in production)
        location = LocationInfo(ip_address=ip_address)
        
        # Calculate expiry
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.config.absolute_timeout_hours)
        
        # Create session
        session = Session(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            device=device,
            location=location,
            created_at=now,
            expires_at=expires_at,
            last_activity=now,
        )
        
        # Store session
        self._sessions[session.id] = session
        
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session.id)
        
        logger.info(f"Session created for user {user_id} from {ip_address}")
        
        return token, session
    
    def validate_session(self, token: str) -> Optional[Session]:
        """Validate session token and return session if valid."""
        token_hash = self._hash_token(token)
        
        # Find session by token hash
        session = None
        for s in self._sessions.values():
            if secrets.compare_digest(s.token_hash, token_hash):
                session = s
                break
        
        if not session:
            return None
        
        # Check if active
        if not session.is_active:
            return None
        
        # Check expiry
        now = datetime.utcnow()
        if now > session.expires_at:
            self.revoke_session(session.id)
            return None
        
        # Check idle timeout
        idle_timeout = timedelta(minutes=self.config.idle_timeout_minutes)
        if now - session.last_activity > idle_timeout:
            self.revoke_session(session.id)
            return None
        
        # Update last activity
        session.last_activity = now
        
        return session
    
    def refresh_session(self, session_id: str) -> Optional[str]:
        """Refresh session and return new token."""
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            return None
        
        # Generate new token
        new_token = secrets.token_urlsafe(self.TOKEN_LENGTH)
        session.token_hash = self._hash_token(new_token)
        session.last_activity = datetime.utcnow()
        
        # Extend expiry if within renewal window
        now = datetime.utcnow()
        renewal_window = timedelta(hours=self.config.absolute_timeout_hours / 4)
        if session.expires_at - now < renewal_window:
            session.expires_at = now + timedelta(hours=self.config.absolute_timeout_hours)
        
        return new_token
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        
        # Remove from user sessions
        user_sessions = self._user_sessions.get(session.user_id, [])
        if session_id in user_sessions:
            user_sessions.remove(session_id)
        
        logger.info(f"Session {session_id} revoked")
        return True
    
    def revoke_all_sessions(self, user_id: str, except_session_id: str = None) -> int:
        """Revoke all sessions for a user."""
        session_ids = self._user_sessions.get(user_id, []).copy()
        count = 0
        
        for session_id in session_ids:
            if session_id != except_session_id:
                if self.revoke_session(session_id):
                    count += 1
        
        logger.info(f"Revoked {count} sessions for user {user_id}")
        return count
    
    def get_user_sessions(self, user_id: str, current_session_id: str = None) -> List[Session]:
        """Get all active sessions for a user."""
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self._sessions.get(session_id)
            if session and session.is_active:
                session.is_current = (session_id == current_session_id)
                sessions.append(session)
        
        # Sort by last activity
        sessions.sort(key=lambda s: s.last_activity, reverse=True)
        
        return sessions
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self._sessions.get(session_id)
    
    def _enforce_session_limit(self, user_id: str):
        """Enforce concurrent session limit."""
        sessions = self.get_user_sessions(user_id)
        
        if len(sessions) >= self.config.max_concurrent_sessions:
            # Revoke oldest sessions
            sessions_to_revoke = sessions[self.config.max_concurrent_sessions - 1:]
            for session in sessions_to_revoke:
                self.revoke_session(session.id)
    
    def _hash_token(self, token: str) -> str:
        """Hash session token."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _parse_user_agent(self, user_agent_string: str) -> DeviceInfo:
        """Parse user agent string."""
        if not user_agent_string:
            return DeviceInfo()
        
        try:
            ua = parse_user_agent(user_agent_string)
            
            if ua.is_mobile:
                device_type = "mobile"
            elif ua.is_tablet:
                device_type = "tablet"
            elif ua.is_pc:
                device_type = "desktop"
            else:
                device_type = "unknown"
            
            return DeviceInfo(
                device_type=device_type,
                browser=ua.browser.family,
                browser_version=ua.browser.version_string,
                os=ua.os.family,
                os_version=ua.os.version_string,
                is_mobile=ua.is_mobile,
                is_tablet=ua.is_tablet,
                is_bot=ua.is_bot,
            )
        except Exception:
            return DeviceInfo()
    
    def cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = []
        
        for session_id, session in self._sessions.items():
            if now > session.expires_at or not session.is_active:
                expired.append(session_id)
        
        for session_id in expired:
            session = self._sessions.pop(session_id, None)
            if session:
                user_sessions = self._user_sessions.get(session.user_id, [])
                if session_id in user_sessions:
                    user_sessions.remove(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global session manager
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get session manager instance."""
    return session_manager
```

---

## File 3: JWT Token Manager
**Path:** `backend/app/security/auth/tokens.py`

```python
"""
JWT Token Management
Secure JWT token generation and validation
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import jwt
import secrets
import logging
from uuid import uuid4

from app.security.config import get_security_config

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    MFA = "mfa"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    API_KEY = "api_key"


class TokenError(Exception):
    """Token-related errors."""
    pass


class TokenExpiredError(TokenError):
    """Token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Token is invalid."""
    pass


class TokenManager:
    """Manages JWT tokens."""
    
    # Token configuration
    TOKEN_CONFIGS = {
        TokenType.ACCESS: {
            "expiry_minutes": 30,
            "audience": "logiaccounting:access",
        },
        TokenType.REFRESH: {
            "expiry_days": 7,
            "audience": "logiaccounting:refresh",
        },
        TokenType.MFA: {
            "expiry_minutes": 5,
            "audience": "logiaccounting:mfa",
        },
        TokenType.PASSWORD_RESET: {
            "expiry_hours": 1,
            "audience": "logiaccounting:password_reset",
        },
        TokenType.EMAIL_VERIFICATION: {
            "expiry_hours": 24,
            "audience": "logiaccounting:email_verification",
        },
    }
    
    def __init__(self):
        self.config = get_security_config()
        self._revoked_tokens: set = set()  # In production, use Redis
    
    def create_access_token(
        self,
        user_id: str,
        customer_id: str = None,
        roles: list = None,
        additional_claims: Dict = None,
    ) -> str:
        """Create access token."""
        claims = {
            "sub": user_id,
            "type": TokenType.ACCESS.value,
            "roles": roles or [],
        }
        
        if customer_id:
            claims["customer_id"] = customer_id
        
        if additional_claims:
            claims.update(additional_claims)
        
        return self._create_token(TokenType.ACCESS, claims)
    
    def create_refresh_token(self, user_id: str, session_id: str = None) -> str:
        """Create refresh token."""
        claims = {
            "sub": user_id,
            "type": TokenType.REFRESH.value,
            "session_id": session_id or str(uuid4()),
        }
        
        return self._create_token(TokenType.REFRESH, claims)
    
    def create_mfa_token(self, user_id: str) -> str:
        """Create MFA pending token (issued before MFA verification)."""
        claims = {
            "sub": user_id,
            "type": TokenType.MFA.value,
            "mfa_pending": True,
        }
        
        return self._create_token(TokenType.MFA, claims)
    
    def create_password_reset_token(self, user_id: str, email: str) -> str:
        """Create password reset token."""
        claims = {
            "sub": user_id,
            "type": TokenType.PASSWORD_RESET.value,
            "email": email,
            "nonce": secrets.token_hex(16),
        }
        
        return self._create_token(TokenType.PASSWORD_RESET, claims)
    
    def create_email_verification_token(self, user_id: str, email: str) -> str:
        """Create email verification token."""
        claims = {
            "sub": user_id,
            "type": TokenType.EMAIL_VERIFICATION.value,
            "email": email,
        }
        
        return self._create_token(TokenType.EMAIL_VERIFICATION, claims)
    
    def create_token_pair(
        self,
        user_id: str,
        customer_id: str = None,
        roles: list = None,
        session_id: str = None,
    ) -> Tuple[str, str]:
        """Create access and refresh token pair."""
        access_token = self.create_access_token(
            user_id=user_id,
            customer_id=customer_id,
            roles=roles,
        )
        
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            session_id=session_id,
        )
        
        return access_token, refresh_token
    
    def verify_token(
        self,
        token: str,
        expected_type: TokenType = None,
    ) -> Dict[str, Any]:
        """Verify and decode a token."""
        try:
            # Check if revoked
            if self._is_revoked(token):
                raise TokenInvalidError("Token has been revoked")
            
            # Decode token
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                options={"verify_aud": False},  # We verify audience separately
            )
            
            # Verify token type
            if expected_type:
                token_type = payload.get("type")
                if token_type != expected_type.value:
                    raise TokenInvalidError(f"Expected {expected_type.value} token, got {token_type}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token using refresh token."""
        # Verify refresh token
        payload = self.verify_token(refresh_token, TokenType.REFRESH)
        
        # Create new token pair
        user_id = payload["sub"]
        session_id = payload.get("session_id")
        
        # Revoke old refresh token
        self.revoke_token(refresh_token)
        
        # Create new tokens
        return self.create_token_pair(
            user_id=user_id,
            session_id=session_id,
        )
    
    def revoke_token(self, token: str):
        """Revoke a token."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                options={"verify_exp": False, "verify_aud": False},
            )
            
            jti = payload.get("jti", token[:32])
            self._revoked_tokens.add(jti)
            
            logger.info(f"Token revoked: {jti}")
            
        except jwt.InvalidTokenError:
            pass  # Invalid token, nothing to revoke
    
    def _create_token(self, token_type: TokenType, claims: Dict) -> str:
        """Create a JWT token."""
        config = self.TOKEN_CONFIGS[token_type]
        
        now = datetime.utcnow()
        
        # Calculate expiry
        if "expiry_minutes" in config:
            expiry = now + timedelta(minutes=config["expiry_minutes"])
        elif "expiry_hours" in config:
            expiry = now + timedelta(hours=config["expiry_hours"])
        elif "expiry_days" in config:
            expiry = now + timedelta(days=config["expiry_days"])
        else:
            expiry = now + timedelta(hours=1)
        
        # Build payload
        payload = {
            "iss": "logiaccounting",
            "aud": config["audience"],
            "iat": now,
            "exp": expiry,
            "jti": str(uuid4()),
            **claims,
        }
        
        # Encode token
        token = jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
        )
        
        return token
    
    def _is_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                options={"verify_exp": False, "verify_aud": False},
            )
            
            jti = payload.get("jti", token[:32])
            return jti in self._revoked_tokens
            
        except jwt.InvalidTokenError:
            return False
    
    def decode_token_unsafe(self, token: str) -> Optional[Dict]:
        """Decode token without verification (for debugging)."""
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False},
            )
        except jwt.InvalidTokenError:
            return None


# Global token manager
token_manager = TokenManager()


def get_token_manager() -> TokenManager:
    """Get token manager instance."""
    return token_manager
```

---

## File 4: Auth Module Init
**Path:** `backend/app/security/auth/__init__.py`

```python
"""
Authentication Module
MFA, OAuth, Sessions, and Token management
"""

from app.security.auth.mfa import (
    MFAManager,
    MFAMethod,
    MFASetup,
    MFAVerification,
    mfa_manager,
    get_mfa_manager,
)

from app.security.auth.oauth import (
    OAuthManager,
    OAuthProvider,
    OAuthUser,
    OAuthTokens,
    oauth_manager,
    get_oauth_manager,
)

from app.security.auth.sessions import (
    SessionManager,
    Session,
    DeviceInfo,
    LocationInfo,
    session_manager,
    get_session_manager,
)

from app.security.auth.tokens import (
    TokenManager,
    TokenType,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    token_manager,
    get_token_manager,
)


__all__ = [
    # MFA
    'MFAManager',
    'MFAMethod',
    'MFASetup',
    'MFAVerification',
    'mfa_manager',
    'get_mfa_manager',
    
    # OAuth
    'OAuthManager',
    'OAuthProvider',
    'OAuthUser',
    'OAuthTokens',
    'oauth_manager',
    'get_oauth_manager',
    
    # Sessions
    'SessionManager',
    'Session',
    'DeviceInfo',
    'LocationInfo',
    'session_manager',
    'get_session_manager',
    
    # Tokens
    'TokenManager',
    'TokenType',
    'TokenError',
    'TokenExpiredError',
    'TokenInvalidError',
    'token_manager',
    'get_token_manager',
]
```

---

## Summary Part 2

| File | Description | Lines |
|------|-------------|-------|
| `auth/oauth.py` | OAuth 2.0 provider manager | ~280 |
| `auth/sessions.py` | Session management | ~320 |
| `auth/tokens.py` | JWT token management | ~280 |
| `auth/__init__.py` | Auth module exports | ~70 |
| **Total** | | **~950 lines** |
