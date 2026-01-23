"""
Portal Authentication Service
Manages customer portal authentication with enhanced security
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import secrets
import logging

from app.models.crm_store import crm_store
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.password import verify_password, hash_password


logger = logging.getLogger(__name__)


class PortalSession:
    """Portal user session"""

    def __init__(self, session_id: str, customer_id: str, contact_id: str, tenant_id: str, device_info: Dict = None):
        self.id = session_id
        self.customer_id = customer_id
        self.contact_id = contact_id
        self.tenant_id = tenant_id
        self.device_info = device_info or {}
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.ip_address = None
        self.user_agent = None


class PortalAuthService:
    """Manages portal authentication and sessions."""

    def __init__(self):
        self._sessions: Dict[str, PortalSession] = {}
        self._portal_users: Dict[str, Dict] = {}
        self._magic_links: Dict[str, Dict] = {}
        self._refresh_tokens: Dict[str, str] = {}

    def register_portal_user(
        self,
        email: str,
        password: str,
        contact_id: str,
        company_id: str,
        tenant_id: str,
        name: str,
    ) -> Dict[str, Any]:
        """Register a new portal user for a contact."""
        if email in self._portal_users:
            raise ValueError("Portal user already exists")

        contact = crm_store.get_contact(contact_id)
        if not contact:
            raise ValueError("Contact not found")

        portal_user = {
            "id": f"pu_{uuid4().hex[:12]}",
            "email": email,
            "password_hash": hash_password(password),
            "contact_id": contact_id,
            "company_id": company_id,
            "tenant_id": tenant_id,
            "name": name,
            "status": "active",
            "two_factor_enabled": False,
            "two_factor_secret": None,
            "preferences": {
                "theme": "system",
                "language": "en",
                "email_notifications": True,
                "push_notifications": False,
            },
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
        }

        self._portal_users[email] = portal_user

        logger.info(f"Portal user registered: {email}")

        return {
            "id": portal_user["id"],
            "email": email,
            "name": name,
        }

    def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Dict[str, Any]:
        """Authenticate portal user."""
        portal_user = self._portal_users.get(email)

        if not portal_user:
            logger.warning(f"Portal login failed - user not found: {email}")
            raise ValueError("Invalid credentials")

        if portal_user["status"] != "active":
            raise ValueError("Account is not active")

        if not verify_password(password, portal_user["password_hash"]):
            logger.warning(f"Portal login failed - wrong password: {email}")
            raise ValueError("Invalid credentials")

        if portal_user["two_factor_enabled"]:
            temp_token = secrets.token_urlsafe(32)
            self._magic_links[temp_token] = {
                "type": "2fa_pending",
                "email": email,
                "expires_at": datetime.utcnow() + timedelta(minutes=5),
            }
            return {
                "requires_2fa": True,
                "temp_token": temp_token,
            }

        return self._create_session(portal_user, ip_address, user_agent)

    def verify_2fa(
        self,
        temp_token: str,
        code: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Dict[str, Any]:
        """Verify 2FA code and complete authentication."""
        link_data = self._magic_links.get(temp_token)

        if not link_data or link_data["type"] != "2fa_pending":
            raise ValueError("Invalid or expired token")

        if datetime.utcnow() > link_data["expires_at"]:
            del self._magic_links[temp_token]
            raise ValueError("Token expired")

        portal_user = self._portal_users.get(link_data["email"])
        if not portal_user:
            raise ValueError("User not found")

        import pyotp
        totp = pyotp.TOTP(portal_user["two_factor_secret"])
        if not totp.verify(code):
            raise ValueError("Invalid 2FA code")

        del self._magic_links[temp_token]

        return self._create_session(portal_user, ip_address, user_agent)

    def _create_session(
        self,
        portal_user: Dict,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Dict[str, Any]:
        """Create a new portal session."""
        session_id = f"ps_{uuid4().hex[:16]}"

        session = PortalSession(
            session_id=session_id,
            customer_id=portal_user["company_id"],
            contact_id=portal_user["contact_id"],
            tenant_id=portal_user["tenant_id"],
        )
        session.ip_address = ip_address
        session.user_agent = user_agent

        self._sessions[session_id] = session

        portal_user["last_login"] = datetime.utcnow().isoformat()

        token_data = {
            "sub": portal_user["id"],
            "email": portal_user["email"],
            "role": "portal_customer",
            "customer_id": portal_user["company_id"],
            "contact_id": portal_user["contact_id"],
            "tenant_id": portal_user["tenant_id"],
            "session_id": session_id,
        }

        access_token = create_access_token(token_data, expires_minutes=15)
        refresh_token = create_refresh_token(token_data, expires_days=7)

        self._refresh_tokens[refresh_token] = session_id

        logger.info(f"Portal session created: {portal_user['email']}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,
            "user": {
                "id": portal_user["id"],
                "email": portal_user["email"],
                "name": portal_user["name"],
                "company_id": portal_user["company_id"],
            },
        }

    def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        session_id = self._refresh_tokens.get(refresh_token)
        if not session_id:
            raise ValueError("Invalid refresh token")

        session = self._sessions.get(session_id)
        if not session:
            del self._refresh_tokens[refresh_token]
            raise ValueError("Session expired")

        portal_user = None
        for user in self._portal_users.values():
            if user["contact_id"] == session.contact_id:
                portal_user = user
                break

        if not portal_user:
            raise ValueError("User not found")

        session.last_active = datetime.utcnow()

        token_data = {
            "sub": portal_user["id"],
            "email": portal_user["email"],
            "role": "portal_customer",
            "customer_id": session.customer_id,
            "contact_id": session.contact_id,
            "tenant_id": session.tenant_id,
            "session_id": session_id,
        }

        access_token = create_access_token(token_data, expires_minutes=15)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900,
        }

    def logout(self, session_id: str):
        """End portal session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

        to_remove = [rt for rt, sid in self._refresh_tokens.items() if sid == session_id]
        for rt in to_remove:
            del self._refresh_tokens[rt]

        logger.info(f"Portal session ended: {session_id}")

    def get_sessions(self, contact_id: str) -> list:
        """Get all active sessions for a contact."""
        return [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "created_at": s.created_at.isoformat(),
                "last_active": s.last_active.isoformat(),
            }
            for s in self._sessions.values()
            if s.contact_id == contact_id
        ]

    def revoke_session(self, session_id: str, contact_id: str):
        """Revoke a specific session."""
        session = self._sessions.get(session_id)
        if session and session.contact_id == contact_id:
            self.logout(session_id)

    def create_magic_link(self, email: str, tenant_id: str) -> str:
        """Create a magic link for passwordless login."""
        portal_user = self._portal_users.get(email)
        if not portal_user or portal_user["tenant_id"] != tenant_id:
            raise ValueError("User not found")

        token = secrets.token_urlsafe(32)
        self._magic_links[token] = {
            "type": "magic_link",
            "email": email,
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
        }

        return token

    def verify_magic_link(
        self,
        token: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Dict[str, Any]:
        """Verify magic link and authenticate."""
        link_data = self._magic_links.get(token)

        if not link_data or link_data["type"] != "magic_link":
            raise ValueError("Invalid or expired link")

        if datetime.utcnow() > link_data["expires_at"]:
            del self._magic_links[token]
            raise ValueError("Link expired")

        portal_user = self._portal_users.get(link_data["email"])
        if not portal_user:
            raise ValueError("User not found")

        del self._magic_links[token]

        return self._create_session(portal_user, ip_address, user_agent)

    def get_portal_user(self, email: str) -> Optional[Dict]:
        """Get portal user by email."""
        user = self._portal_users.get(email)
        if user:
            return {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "contact_id": user["contact_id"],
                "company_id": user["company_id"],
                "tenant_id": user["tenant_id"],
                "status": user["status"],
                "preferences": user["preferences"],
                "two_factor_enabled": user["two_factor_enabled"],
                "last_login": user["last_login"],
            }
        return None

    def update_preferences(self, email: str, preferences: Dict) -> Dict:
        """Update portal user preferences."""
        portal_user = self._portal_users.get(email)
        if not portal_user:
            raise ValueError("User not found")

        portal_user["preferences"].update(preferences)
        return portal_user["preferences"]

    def change_password(self, email: str, current_password: str, new_password: str):
        """Change portal user password."""
        portal_user = self._portal_users.get(email)
        if not portal_user:
            raise ValueError("User not found")

        if not verify_password(current_password, portal_user["password_hash"]):
            raise ValueError("Current password is incorrect")

        portal_user["password_hash"] = hash_password(new_password)
        logger.info(f"Portal password changed: {email}")


portal_auth_service = PortalAuthService()
