"""
Session Management Routes
Provides endpoints for managing user sessions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, status, Query
from pydantic import BaseModel, Field

from app.utils.auth import get_current_user, require_roles


router = APIRouter()


class SessionInfo(BaseModel):
    """Information about a user session."""
    id: str
    user_id: str
    device: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    created_at: str
    last_activity: str
    expires_at: str
    is_current: bool = False


class SessionListResponse(BaseModel):
    """Response for session list."""
    success: bool = True
    sessions: List[SessionInfo]
    total: int


class SessionDetailResponse(BaseModel):
    """Response for single session details."""
    success: bool = True
    session: SessionInfo


class SessionRevokeResponse(BaseModel):
    """Response for session revocation."""
    success: bool = True
    message: str
    revoked_count: int = 1


class SessionActivityResponse(BaseModel):
    """Response for session activity."""
    success: bool = True
    activities: List[Dict[str, Any]]
    total: int


class SessionSettingsRequest(BaseModel):
    """Request to update session settings."""
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=1440)
    max_concurrent_sessions: Optional[int] = Field(None, ge=1, le=10)
    require_reauth_for_sensitive: Optional[bool] = None
    remember_device: Optional[bool] = None


class SessionSettingsResponse(BaseModel):
    """Response for session settings."""
    success: bool = True
    settings: Dict[str, Any]


class SessionStore:
    """In-memory session storage."""

    _instance = None
    _sessions: Dict[str, Dict[str, Any]] = {}
    _user_sessions: Dict[str, List[str]] = {}
    _activities: Dict[str, List[Dict[str, Any]]] = {}
    _settings: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._sessions = {}
            cls._user_sessions = {}
            cls._activities = {}
            cls._settings = {}
        return cls._instance

    def create_session(
        self,
        session_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        ttl_minutes: int = 60,
    ) -> Dict[str, Any]:
        """Create a new session."""
        now = datetime.utcnow()
        device_info = self._parse_user_agent(user_agent or "")

        session = {
            "id": session_id,
            "user_id": user_id,
            "device": device_info.get("device"),
            "browser": device_info.get("browser"),
            "os": device_info.get("os"),
            "ip_address": ip_address,
            "location": self._get_location(ip_address),
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "expires_at": (now + timedelta(minutes=ttl_minutes)).isoformat(),
            "user_agent": user_agent,
        }

        self._sessions[session_id] = session

        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)

        self._log_activity(session_id, "session_created", {"ip_address": ip_address})

        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        if session:
            expires_at = datetime.fromisoformat(session["expires_at"])
            if datetime.utcnow() > expires_at:
                self.revoke_session(session_id)
                return None
        return session

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []
        for sid in session_ids:
            session = self.get_session(sid)
            if session:
                sessions.append(session)
        return sessions

    def update_activity(self, session_id: str):
        """Update last activity timestamp for a session."""
        session = self._sessions.get(session_id)
        if session:
            session["last_activity"] = datetime.utcnow().isoformat()

    def revoke_session(self, session_id: str) -> bool:
        """Revoke a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        user_id = session["user_id"]
        if user_id in self._user_sessions:
            self._user_sessions[user_id] = [
                sid for sid in self._user_sessions[user_id] if sid != session_id
            ]

        self._log_activity(session_id, "session_revoked", {})
        del self._sessions[session_id]

        return True

    def revoke_all_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> int:
        """Revoke all sessions for a user."""
        session_ids = self._user_sessions.get(user_id, []).copy()
        revoked = 0

        for sid in session_ids:
            if except_session_id and sid == except_session_id:
                continue
            if self.revoke_session(sid):
                revoked += 1

        return revoked

    def get_session_activities(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get activities for a session."""
        activities = self._activities.get(session_id, [])
        return sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_settings(self, user_id: str) -> Dict[str, Any]:
        """Get session settings for a user."""
        defaults = {
            "session_timeout_minutes": 60,
            "max_concurrent_sessions": 5,
            "require_reauth_for_sensitive": True,
            "remember_device": False,
        }
        user_settings = self._settings.get(user_id, {})
        return {**defaults, **user_settings}

    def update_settings(self, user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update session settings for a user."""
        if user_id not in self._settings:
            self._settings[user_id] = {}

        for key, value in settings.items():
            if value is not None:
                self._settings[user_id][key] = value

        return self.get_settings(user_id)

    def _parse_user_agent(self, user_agent: str) -> Dict[str, Optional[str]]:
        """Parse user agent string to extract device info."""
        result = {"device": None, "browser": None, "os": None}

        if "Mobile" in user_agent or "Android" in user_agent:
            result["device"] = "Mobile"
        elif "Tablet" in user_agent or "iPad" in user_agent:
            result["device"] = "Tablet"
        else:
            result["device"] = "Desktop"

        if "Chrome" in user_agent and "Edg" not in user_agent:
            result["browser"] = "Chrome"
        elif "Firefox" in user_agent:
            result["browser"] = "Firefox"
        elif "Safari" in user_agent and "Chrome" not in user_agent:
            result["browser"] = "Safari"
        elif "Edg" in user_agent:
            result["browser"] = "Edge"
        else:
            result["browser"] = "Other"

        if "Windows" in user_agent:
            result["os"] = "Windows"
        elif "Mac OS" in user_agent:
            result["os"] = "macOS"
        elif "Linux" in user_agent:
            result["os"] = "Linux"
        elif "Android" in user_agent:
            result["os"] = "Android"
        elif "iOS" in user_agent or "iPhone" in user_agent:
            result["os"] = "iOS"
        else:
            result["os"] = "Other"

        return result

    def _get_location(self, ip_address: Optional[str]) -> Optional[str]:
        """Get location from IP address."""
        if not ip_address or ip_address in ["127.0.0.1", "localhost", "::1"]:
            return "Local"
        return "Unknown"

    def _log_activity(self, session_id: str, action: str, details: Dict[str, Any]):
        """Log session activity."""
        if session_id not in self._activities:
            self._activities[session_id] = []

        self._activities[session_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
        })


session_store = SessionStore()


def get_client_info(request: Request) -> Dict[str, Optional[str]]:
    """Extract client information from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None

    return {
        "ip_address": ip_address,
        "user_agent": request.headers.get("User-Agent"),
    }


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """List all active sessions for the current user."""
    sessions = session_store.get_user_sessions(current_user["id"])

    current_session_id = None
    if hasattr(request.state, "session_id"):
        current_session_id = request.state.session_id

    session_list = []
    for session in sessions:
        session_info = SessionInfo(
            id=session["id"],
            user_id=session["user_id"],
            device=session.get("device"),
            browser=session.get("browser"),
            os=session.get("os"),
            ip_address=session.get("ip_address"),
            location=session.get("location"),
            created_at=session["created_at"],
            last_activity=session["last_activity"],
            expires_at=session["expires_at"],
            is_current=session["id"] == current_session_id,
        )
        session_list.append(session_info)

    return SessionListResponse(
        sessions=session_list,
        total=len(session_list),
    )


@router.get("/current", response_model=SessionDetailResponse)
async def get_current_session(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Get details of the current session."""
    current_session_id = getattr(request.state, "session_id", None)

    if not current_session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current session not found",
        )

    session = session_store.get_session(current_session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )

    return SessionDetailResponse(
        session=SessionInfo(
            id=session["id"],
            user_id=session["user_id"],
            device=session.get("device"),
            browser=session.get("browser"),
            os=session.get("os"),
            ip_address=session.get("ip_address"),
            location=session.get("location"),
            created_at=session["created_at"],
            last_activity=session["last_activity"],
            expires_at=session["expires_at"],
            is_current=True,
        ),
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get details of a specific session."""
    session = session_store.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )

    return SessionDetailResponse(
        session=SessionInfo(
            id=session["id"],
            user_id=session["user_id"],
            device=session.get("device"),
            browser=session.get("browser"),
            os=session.get("os"),
            ip_address=session.get("ip_address"),
            location=session.get("location"),
            created_at=session["created_at"],
            last_activity=session["last_activity"],
            expires_at=session["expires_at"],
        ),
    )


@router.delete("/{session_id}", response_model=SessionRevokeResponse)
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Revoke a specific session."""
    session = session_store.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )

    session_store.revoke_session(session_id)

    return SessionRevokeResponse(
        message="Session revoked successfully",
    )


@router.delete("", response_model=SessionRevokeResponse)
async def revoke_all_sessions(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    except_current: bool = Query(default=True, description="Keep current session active"),
):
    """Revoke all sessions for the current user."""
    current_session_id = None
    if except_current and hasattr(request.state, "session_id"):
        current_session_id = request.state.session_id

    revoked = session_store.revoke_all_sessions(
        current_user["id"],
        except_session_id=current_session_id,
    )

    return SessionRevokeResponse(
        message=f"Revoked {revoked} session(s)",
        revoked_count=revoked,
    )


@router.get("/{session_id}/activity", response_model=SessionActivityResponse)
async def get_session_activity(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=50, le=200),
):
    """Get activity log for a specific session."""
    session = session_store.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )

    activities = session_store.get_session_activities(session_id, limit)

    return SessionActivityResponse(
        activities=activities,
        total=len(activities),
    )


@router.get("/settings/current", response_model=SessionSettingsResponse)
async def get_session_settings(current_user: dict = Depends(get_current_user)):
    """Get session settings for the current user."""
    settings = session_store.get_settings(current_user["id"])
    return SessionSettingsResponse(settings=settings)


@router.put("/settings/current", response_model=SessionSettingsResponse)
async def update_session_settings(
    request: SessionSettingsRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update session settings for the current user."""
    updates = request.model_dump(exclude_unset=True)
    settings = session_store.update_settings(current_user["id"], updates)
    return SessionSettingsResponse(settings=settings)


@router.get("/admin/users/{user_id}", response_model=SessionListResponse)
async def admin_list_user_sessions(
    user_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """List all sessions for a specific user (admin only)."""
    sessions = session_store.get_user_sessions(user_id)

    session_list = [
        SessionInfo(
            id=s["id"],
            user_id=s["user_id"],
            device=s.get("device"),
            browser=s.get("browser"),
            os=s.get("os"),
            ip_address=s.get("ip_address"),
            location=s.get("location"),
            created_at=s["created_at"],
            last_activity=s["last_activity"],
            expires_at=s["expires_at"],
        )
        for s in sessions
    ]

    return SessionListResponse(
        sessions=session_list,
        total=len(session_list),
    )


@router.delete("/admin/users/{user_id}", response_model=SessionRevokeResponse)
async def admin_revoke_user_sessions(
    user_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Revoke all sessions for a specific user (admin only)."""
    revoked = session_store.revoke_all_sessions(user_id)

    return SessionRevokeResponse(
        message=f"Revoked all {revoked} session(s) for user {user_id}",
        revoked_count=revoked,
    )


@router.delete("/admin/sessions/{session_id}", response_model=SessionRevokeResponse)
async def admin_revoke_session(
    session_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Revoke a specific session by ID (admin only)."""
    session = session_store.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session_store.revoke_session(session_id)

    return SessionRevokeResponse(
        message="Session revoked successfully",
    )
