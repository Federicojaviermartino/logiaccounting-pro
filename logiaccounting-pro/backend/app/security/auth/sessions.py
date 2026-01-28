"""
Session Manager
Session management with device tracking for LogiAccounting Pro
"""

import secrets
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging
import json

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Client device information."""
    device_id: str
    device_type: str = "unknown"
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    is_mobile: bool = False
    is_tablet: bool = False

    @classmethod
    def from_user_agent(cls, user_agent: str, device_id: Optional[str] = None) -> "DeviceInfo":
        """Parse device info from user agent string."""
        if device_id is None:
            device_id = hashlib.sha256(user_agent.encode()).hexdigest()[:32]

        ua_lower = user_agent.lower()

        browser = None
        browser_version = None
        if "firefox" in ua_lower:
            browser = "Firefox"
        elif "edg" in ua_lower:
            browser = "Edge"
        elif "chrome" in ua_lower:
            browser = "Chrome"
        elif "safari" in ua_lower:
            browser = "Safari"
        elif "opera" in ua_lower:
            browser = "Opera"

        os_name = None
        os_version = None
        if "windows" in ua_lower:
            os_name = "Windows"
        elif "mac os" in ua_lower or "macos" in ua_lower:
            os_name = "macOS"
        elif "linux" in ua_lower:
            os_name = "Linux"
        elif "android" in ua_lower:
            os_name = "Android"
        elif "ios" in ua_lower or "iphone" in ua_lower or "ipad" in ua_lower:
            os_name = "iOS"

        is_mobile = any(x in ua_lower for x in ["mobile", "android", "iphone"])
        is_tablet = any(x in ua_lower for x in ["tablet", "ipad"])

        device_type = "mobile" if is_mobile else "tablet" if is_tablet else "desktop"

        return cls(
            device_id=device_id,
            device_type=device_type,
            browser=browser,
            browser_version=browser_version,
            os_name=os_name,
            os_version=os_version,
            is_mobile=is_mobile,
            is_tablet=is_tablet,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "browser": self.browser,
            "browser_version": self.browser_version,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "is_mobile": self.is_mobile,
            "is_tablet": self.is_tablet,
        }


@dataclass
class SessionData:
    """Session data structure."""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[DeviceInfo] = None
    is_active: bool = True
    mfa_verified: bool = False
    mfa_verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return utc_now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if session is valid."""
        return self.is_active and not self.is_expired()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = utc_now()

    def extend(self, minutes: int) -> None:
        """Extend session expiration."""
        self.expires_at = utc_now() + timedelta(minutes=minutes)
        self.update_activity()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ip_address": self.ip_address,
            "device_info": self.device_info.to_dict() if self.device_info else None,
            "is_active": self.is_active,
            "mfa_verified": self.mfa_verified,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        data = self.to_dict()
        data["user_agent"] = self.user_agent
        data["mfa_verified_at"] = self.mfa_verified_at.isoformat() if self.mfa_verified_at else None
        data["metadata"] = self.metadata
        return json.dumps(data)

    @classmethod
    def from_json(cls, data: str) -> "SessionData":
        """Create from JSON string."""
        parsed = json.loads(data)

        device_info = None
        if parsed.get("device_info"):
            device_info = DeviceInfo(**parsed["device_info"])

        return cls(
            session_id=parsed["session_id"],
            user_id=parsed["user_id"],
            created_at=datetime.fromisoformat(parsed["created_at"]),
            last_activity=datetime.fromisoformat(parsed["last_activity"]),
            expires_at=datetime.fromisoformat(parsed["expires_at"]),
            ip_address=parsed.get("ip_address"),
            user_agent=parsed.get("user_agent"),
            device_info=device_info,
            is_active=parsed.get("is_active", True),
            mfa_verified=parsed.get("mfa_verified", False),
            mfa_verified_at=datetime.fromisoformat(parsed["mfa_verified_at"]) if parsed.get("mfa_verified_at") else None,
            metadata=parsed.get("metadata", {}),
        )


class SessionManager:
    """
    Session Manager with device tracking.
    Supports both in-memory and Redis-backed storage.
    """

    def __init__(
        self,
        session_timeout_minutes: int = 30,
        absolute_timeout_hours: int = 24,
        max_concurrent_sessions: int = 5,
        bind_to_ip: bool = False,
        bind_to_user_agent: bool = True,
        redis_client: Optional[Any] = None,
        session_prefix: str = "session:",
    ):
        self.session_timeout_minutes = session_timeout_minutes
        self.absolute_timeout_hours = absolute_timeout_hours
        self.max_concurrent_sessions = max_concurrent_sessions
        self.bind_to_ip = bind_to_ip
        self.bind_to_user_agent = bind_to_user_agent
        self.redis = redis_client
        self.session_prefix = session_prefix

        self._sessions: Dict[str, SessionData] = {}
        self._user_sessions: Dict[str, List[str]] = {}

    def _generate_session_id(self) -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)

    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for a session."""
        return f"{self.session_prefix}{session_id}"

    def _get_user_sessions_key(self, user_id: str) -> str:
        """Get Redis key for user sessions list."""
        return f"{self.session_prefix}user:{user_id}"

    async def create_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[DeviceInfo] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionData:
        """
        Create a new session for a user.

        Args:
            user_id: The user ID
            ip_address: Client IP address
            user_agent: Client user agent
            device_info: Parsed device information
            metadata: Additional session metadata

        Returns:
            SessionData for the new session
        """
        await self._enforce_session_limit(user_id)

        session_id = self._generate_session_id()
        now = utc_now()

        if device_info is None and user_agent:
            device_info = DeviceInfo.from_user_agent(user_agent)

        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=self.absolute_timeout_hours),
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            metadata=metadata or {},
        )

        await self._store_session(session)

        logger.info(f"Created session {session_id[:8]}... for user {user_id}")

        return session

    async def _store_session(self, session: SessionData) -> None:
        """Store session in backend."""
        if self.redis:
            key = self._get_session_key(session.session_id)
            ttl = int((session.expires_at - utc_now()).total_seconds())
            await self.redis.setex(key, ttl, session.to_json())

            user_key = self._get_user_sessions_key(session.user_id)
            await self.redis.sadd(user_key, session.session_id)
            await self.redis.expire(user_key, self.absolute_timeout_hours * 3600)
        else:
            self._sessions[session.session_id] = session

            if session.user_id not in self._user_sessions:
                self._user_sessions[session.user_id] = []
            self._user_sessions[session.user_id].append(session.session_id)

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID."""
        if self.redis:
            key = self._get_session_key(session_id)
            data = await self.redis.get(key)
            if data:
                return SessionData.from_json(data)
            return None
        else:
            return self._sessions.get(session_id)

    async def validate_session(
        self,
        session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[SessionData]:
        """
        Validate a session and update activity.

        Args:
            session_id: The session ID
            ip_address: Current client IP
            user_agent: Current client user agent

        Returns:
            SessionData if valid, None otherwise
        """
        session = await self.get_session(session_id)

        if session is None:
            logger.debug(f"Session not found: {session_id[:8]}...")
            return None

        if not session.is_valid():
            logger.debug(f"Session invalid or expired: {session_id[:8]}...")
            await self.destroy_session(session_id)
            return None

        if self.bind_to_ip and ip_address and session.ip_address != ip_address:
            logger.warning(
                f"Session IP mismatch: expected {session.ip_address}, got {ip_address}"
            )
            await self.destroy_session(session_id)
            return None

        if self.bind_to_user_agent and user_agent:
            if session.user_agent and session.user_agent != user_agent:
                logger.warning(f"Session user agent mismatch for {session_id[:8]}...")

        session.update_activity()
        await self._store_session(session)

        return session

    async def extend_session(
        self,
        session_id: str,
        minutes: Optional[int] = None,
    ) -> bool:
        """Extend session expiration."""
        session = await self.get_session(session_id)

        if session is None or not session.is_valid():
            return False

        extension = minutes or self.session_timeout_minutes

        max_expiry = session.created_at + timedelta(hours=self.absolute_timeout_hours)
        new_expiry = utc_now() + timedelta(minutes=extension)

        if new_expiry > max_expiry:
            new_expiry = max_expiry

        session.expires_at = new_expiry
        session.update_activity()
        await self._store_session(session)

        logger.debug(f"Extended session {session_id[:8]}... by {extension} minutes")

        return True

    async def mark_mfa_verified(self, session_id: str) -> bool:
        """Mark session as MFA verified."""
        session = await self.get_session(session_id)

        if session is None or not session.is_valid():
            return False

        session.mfa_verified = True
        session.mfa_verified_at = utc_now()
        await self._store_session(session)

        logger.info(f"Session {session_id[:8]}... marked as MFA verified")

        return True

    async def destroy_session(self, session_id: str) -> bool:
        """Destroy a session."""
        session = await self.get_session(session_id)

        if session is None:
            return False

        if self.redis:
            key = self._get_session_key(session_id)
            await self.redis.delete(key)

            user_key = self._get_user_sessions_key(session.user_id)
            await self.redis.srem(user_key, session_id)
        else:
            if session_id in self._sessions:
                del self._sessions[session_id]

            if session.user_id in self._user_sessions:
                if session_id in self._user_sessions[session.user_id]:
                    self._user_sessions[session.user_id].remove(session_id)

        logger.info(f"Destroyed session {session_id[:8]}...")

        return True

    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user."""
        sessions = []

        if self.redis:
            user_key = self._get_user_sessions_key(user_id)
            session_ids = await self.redis.smembers(user_key)

            for session_id in session_ids:
                session = await self.get_session(session_id.decode() if isinstance(session_id, bytes) else session_id)
                if session and session.is_valid():
                    sessions.append(session)
        else:
            session_ids = self._user_sessions.get(user_id, [])
            for session_id in session_ids:
                session = self._sessions.get(session_id)
                if session and session.is_valid():
                    sessions.append(session)

        return sessions

    async def destroy_user_sessions(
        self,
        user_id: str,
        except_session: Optional[str] = None,
    ) -> int:
        """
        Destroy all sessions for a user.

        Args:
            user_id: The user ID
            except_session: Session ID to keep

        Returns:
            Number of sessions destroyed
        """
        sessions = await self.get_user_sessions(user_id)
        count = 0

        for session in sessions:
            if except_session and session.session_id == except_session:
                continue
            await self.destroy_session(session.session_id)
            count += 1

        if count > 0:
            logger.info(f"Destroyed {count} sessions for user {user_id}")

        return count

    async def _enforce_session_limit(self, user_id: str) -> None:
        """Enforce maximum concurrent sessions limit."""
        sessions = await self.get_user_sessions(user_id)

        if len(sessions) >= self.max_concurrent_sessions:
            sessions.sort(key=lambda s: s.last_activity)

            sessions_to_remove = len(sessions) - self.max_concurrent_sessions + 1
            for i in range(sessions_to_remove):
                await self.destroy_session(sessions[i].session_id)

            logger.info(
                f"Removed {sessions_to_remove} old sessions for user {user_id} "
                f"due to session limit"
            )

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions removed
        """
        if self.redis:
            return 0

        count = 0
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]

        for session_id in expired:
            session = self._sessions[session_id]
            if session.user_id in self._user_sessions:
                if session_id in self._user_sessions[session.user_id]:
                    self._user_sessions[session.user_id].remove(session_id)
            del self._sessions[session_id]
            count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")

        return count

    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        if self.redis:
            keys = await self.redis.keys(f"{self.session_prefix}*")
            session_count = len([k for k in keys if b"user:" not in k])
            user_count = len([k for k in keys if b"user:" in k])
        else:
            session_count = len(self._sessions)
            user_count = len(self._user_sessions)

        return {
            "total_sessions": session_count,
            "total_users_with_sessions": user_count,
            "session_timeout_minutes": self.session_timeout_minutes,
            "absolute_timeout_hours": self.absolute_timeout_hours,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "using_redis": self.redis is not None,
        }

    async def rotate_session(
        self,
        old_session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[SessionData]:
        """
        Rotate session ID while preserving session data.
        Used after authentication events for security.

        Returns:
            New SessionData or None if old session invalid
        """
        old_session = await self.get_session(old_session_id)

        if old_session is None or not old_session.is_valid():
            return None

        new_session = await self.create_session(
            user_id=old_session.user_id,
            ip_address=ip_address or old_session.ip_address,
            user_agent=user_agent or old_session.user_agent,
            device_info=old_session.device_info,
            metadata=old_session.metadata,
        )

        new_session.mfa_verified = old_session.mfa_verified
        new_session.mfa_verified_at = old_session.mfa_verified_at
        await self._store_session(new_session)

        await self.destroy_session(old_session_id)

        logger.info(
            f"Rotated session {old_session_id[:8]}... -> {new_session.session_id[:8]}..."
        )

        return new_session
