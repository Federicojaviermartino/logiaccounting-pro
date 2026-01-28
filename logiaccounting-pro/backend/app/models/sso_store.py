"""
SSO Data Stores for LogiAccounting Pro
Stores SSO connections, sessions, and external identities
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from app.utils.encryption import encrypt_value, decrypt_value
from app.utils.datetime_utils import utc_now


class SSOConnectionStore:
    """Store for SSO connection configurations"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Find all connections with optional filters"""
        results = self._data.copy()
        if filters:
            if filters.get("organization_id"):
                results = [c for c in results if c.get("organization_id") == filters["organization_id"]]
            if filters.get("status"):
                results = [c for c in results if c.get("status") == filters["status"]]
            if filters.get("protocol"):
                results = [c for c in results if c.get("protocol") == filters["protocol"]]
            if filters.get("provider"):
                results = [c for c in results if c.get("provider") == filters["provider"]]
        return results

    def find_by_id(self, connection_id: str) -> Optional[Dict]:
        """Find connection by ID"""
        return next((c for c in self._data if c["id"] == connection_id), None)

    def find_by_domain(self, domain: str) -> List[Dict]:
        """Find active connections that allow a specific domain"""
        results = []
        domain_lower = domain.lower()
        for conn in self._data:
            if conn.get("status") != "active":
                continue
            allowed = conn.get("allowed_domains", [])
            if not allowed or domain_lower in [d.lower() for d in allowed]:
                results.append(conn)
        return results

    def create(self, data: Dict) -> Dict:
        """Create a new SSO connection"""
        connection = {
            "id": str(uuid4()),
            "organization_id": data.get("organization_id"),
            "name": data.get("name"),
            "protocol": data.get("protocol", "saml"),
            "provider": data.get("provider", "custom"),
            "status": data.get("status", "inactive"),
            "saml_entity_id": data.get("saml_entity_id"),
            "saml_sso_url": data.get("saml_sso_url"),
            "saml_slo_url": data.get("saml_slo_url"),
            "saml_certificate": data.get("saml_certificate"),
            "saml_sign_request": data.get("saml_sign_request", True),
            "saml_want_assertions_signed": data.get("saml_want_assertions_signed", True),
            "saml_name_id_format": data.get("saml_name_id_format", "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"),
            "oauth_client_id": data.get("oauth_client_id"),
            "oauth_client_secret_encrypted": encrypt_value(data.get("oauth_client_secret")) if data.get("oauth_client_secret") else None,
            "oauth_authorization_url": data.get("oauth_authorization_url"),
            "oauth_token_url": data.get("oauth_token_url"),
            "oauth_userinfo_url": data.get("oauth_userinfo_url"),
            "oauth_scopes": data.get("oauth_scopes", "openid profile email"),
            "oidc_discovery_url": data.get("oidc_discovery_url"),
            "oidc_jwks_uri": data.get("oidc_jwks_uri"),
            "attribute_mapping": data.get("attribute_mapping", {
                "email": "email",
                "first_name": "given_name",
                "last_name": "family_name",
                "groups": "groups"
            }),
            "role_mapping": data.get("role_mapping", {}),
            "default_role": data.get("default_role", "client"),
            "scim_enabled": data.get("scim_enabled", False),
            "scim_token_encrypted": encrypt_value(data.get("scim_token")) if data.get("scim_token") else None,
            "scim_sync_groups": data.get("scim_sync_groups", False),
            "allowed_domains": data.get("allowed_domains", []),
            "enforce_sso": data.get("enforce_sso", False),
            "allow_idp_initiated": data.get("allow_idp_initiated", True),
            "session_duration_hours": data.get("session_duration_hours", 8),
            "metadata_url": data.get("metadata_url"),
            "metadata_xml": data.get("metadata_xml"),
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            "last_used_at": None
        }
        self._data.append(connection)
        return self._mask_secrets(connection)

    def update(self, connection_id: str, data: Dict) -> Optional[Dict]:
        """Update an existing connection"""
        for i, conn in enumerate(self._data):
            if conn["id"] == connection_id:
                if "oauth_client_secret" in data:
                    data["oauth_client_secret_encrypted"] = encrypt_value(data.pop("oauth_client_secret"))
                if "scim_token" in data:
                    data["scim_token_encrypted"] = encrypt_value(data.pop("scim_token"))
                self._data[i] = {**conn, **data, "updated_at": utc_now().isoformat()}
                return self._mask_secrets(self._data[i])
        return None

    def delete(self, connection_id: str) -> bool:
        """Delete a connection"""
        for i, conn in enumerate(self._data):
            if conn["id"] == connection_id:
                self._data.pop(i)
                return True
        return False

    def get_oauth_secret(self, connection_id: str) -> Optional[str]:
        """Get decrypted OAuth client secret"""
        conn = self.find_by_id(connection_id)
        if conn and conn.get("oauth_client_secret_encrypted"):
            return decrypt_value(conn["oauth_client_secret_encrypted"])
        return None

    def get_scim_token(self, connection_id: str) -> Optional[str]:
        """Get decrypted SCIM token"""
        conn = self.find_by_id(connection_id)
        if conn and conn.get("scim_token_encrypted"):
            return decrypt_value(conn["scim_token_encrypted"])
        return None

    def validate_scim_token(self, token: str) -> Optional[Dict]:
        """Validate SCIM token and return connection"""
        import hashlib
        for conn in self._data:
            if not conn.get("scim_enabled"):
                continue
            stored = conn.get("scim_token_encrypted")
            if stored:
                decrypted = decrypt_value(stored)
                if decrypted == token:
                    return conn
        return None

    def update_last_used(self, connection_id: str):
        """Update last used timestamp"""
        for conn in self._data:
            if conn["id"] == connection_id:
                conn["last_used_at"] = utc_now().isoformat()
                break

    def map_user_role(self, connection_id: str, groups: List[str]) -> str:
        """Map IdP groups to application role"""
        conn = self.find_by_id(connection_id)
        if not conn:
            return "client"
        role_mapping = conn.get("role_mapping", {})
        if role_mapping and groups:
            for idp_group, app_role in role_mapping.items():
                if idp_group in groups:
                    return app_role
        return conn.get("default_role", "client")

    def is_domain_allowed(self, connection_id: str, email: str) -> bool:
        """Check if email domain is allowed"""
        conn = self.find_by_id(connection_id)
        if not conn:
            return False
        allowed = conn.get("allowed_domains", [])
        if not allowed:
            return True
        domain = email.split("@")[1].lower() if "@" in email else ""
        return domain in [d.lower() for d in allowed]

    def _mask_secrets(self, conn: Dict) -> Dict:
        """Mask sensitive fields for API response"""
        result = conn.copy()
        if result.get("oauth_client_secret_encrypted"):
            result["oauth_client_secret"] = "********"
        result.pop("oauth_client_secret_encrypted", None)
        if result.get("scim_token_encrypted"):
            result["scim_token"] = "********"
        result.pop("scim_token_encrypted", None)
        return result


class SSOSessionStore:
    """Store for SSO sessions"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Create a new SSO session"""
        duration_hours = data.get("duration_hours", 8)
        session = {
            "id": str(uuid4()),
            "user_id": data.get("user_id"),
            "connection_id": data.get("connection_id"),
            "session_index": data.get("session_index"),
            "name_id": data.get("name_id"),
            "name_id_format": data.get("name_id_format"),
            "access_token_encrypted": encrypt_value(data.get("access_token")) if data.get("access_token") else None,
            "refresh_token_encrypted": encrypt_value(data.get("refresh_token")) if data.get("refresh_token") else None,
            "id_token": data.get("id_token"),
            "token_expires_at": data.get("token_expires_at"),
            "is_active": True,
            "created_at": utc_now().isoformat(),
            "last_activity_at": utc_now().isoformat(),
            "expires_at": (utc_now() + timedelta(hours=duration_hours)).isoformat()
        }
        self._data.append(session)
        return session

    def find_by_id(self, session_id: str) -> Optional[Dict]:
        """Find session by ID"""
        return next((s for s in self._data if s["id"] == session_id), None)

    def find_active(self, user_id: str, connection_id: str = None) -> Optional[Dict]:
        """Find active session for user"""
        now = utc_now().isoformat()
        for session in self._data:
            if session["user_id"] != user_id:
                continue
            if connection_id and session["connection_id"] != connection_id:
                continue
            if not session.get("is_active"):
                continue
            if session.get("expires_at", "") < now:
                continue
            return session
        return None

    def update_activity(self, session_id: str):
        """Update session activity timestamp"""
        for session in self._data:
            if session["id"] == session_id:
                session["last_activity_at"] = utc_now().isoformat()
                break

    def invalidate(self, session_id: str):
        """Invalidate a session"""
        for session in self._data:
            if session["id"] == session_id:
                session["is_active"] = False
                break

    def invalidate_user_sessions(self, user_id: str, connection_id: str = None):
        """Invalidate all sessions for a user"""
        for session in self._data:
            if session["user_id"] != user_id:
                continue
            if connection_id and session["connection_id"] != connection_id:
                continue
            session["is_active"] = False

    def get_access_token(self, session_id: str) -> Optional[str]:
        """Get decrypted access token"""
        session = self.find_by_id(session_id)
        if session and session.get("access_token_encrypted"):
            return decrypt_value(session["access_token_encrypted"])
        return None

    def get_refresh_token(self, session_id: str) -> Optional[str]:
        """Get decrypted refresh token"""
        session = self.find_by_id(session_id)
        if session and session.get("refresh_token_encrypted"):
            return decrypt_value(session["refresh_token_encrypted"])
        return None


class UserExternalIdentityStore:
    """Store for user external identity links"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_by_external_id(self, connection_id: str, external_id: str) -> Optional[Dict]:
        """Find identity by external ID"""
        return next(
            (i for i in self._data if i["connection_id"] == connection_id and i["external_id"] == external_id),
            None
        )

    def find_by_user(self, user_id: str) -> List[Dict]:
        """Find all identities for a user"""
        return [i for i in self._data if i["user_id"] == user_id]

    def create(self, data: Dict) -> Dict:
        """Create a new external identity link"""
        identity = {
            "id": str(uuid4()),
            "user_id": data.get("user_id"),
            "connection_id": data.get("connection_id"),
            "external_id": data.get("external_id"),
            "provider_user_id": data.get("provider_user_id"),
            "email": data.get("email"),
            "profile_data": data.get("profile_data", {}),
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            "last_login_at": utc_now().isoformat()
        }
        self._data.append(identity)
        return identity

    def find_or_create(self, user_id: str, connection_id: str, external_id: str, **kwargs) -> Dict:
        """Find existing or create new identity"""
        existing = self.find_by_external_id(connection_id, external_id)
        if existing:
            for key, value in kwargs.items():
                if value is not None:
                    existing[key] = value
            existing["last_login_at"] = utc_now().isoformat()
            existing["updated_at"] = utc_now().isoformat()
            return existing

        return self.create({
            "user_id": user_id,
            "connection_id": connection_id,
            "external_id": external_id,
            **kwargs
        })

    def delete(self, identity_id: str) -> bool:
        """Delete an identity link"""
        for i, identity in enumerate(self._data):
            if identity["id"] == identity_id:
                self._data.pop(i)
                return True
        return False


class SCIMSyncLogStore:
    """Store for SCIM sync operation logs"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def log_operation(
        self,
        connection_id: str,
        operation: str,
        resource_type: str,
        status: str,
        external_id: str = None,
        internal_id: str = None,
        error_message: str = None,
        request_payload: Dict = None,
        response_payload: Dict = None
    ) -> Dict:
        """Log a SCIM operation"""
        log = {
            "id": str(uuid4()),
            "connection_id": connection_id,
            "operation": operation,
            "resource_type": resource_type,
            "status": status,
            "external_id": external_id,
            "internal_id": internal_id,
            "error_message": error_message,
            "request_payload": request_payload,
            "response_payload": response_payload,
            "created_at": utc_now().isoformat()
        }
        self._data.append(log)
        return log

    def get_recent(self, connection_id: str, limit: int = 100) -> List[Dict]:
        """Get recent logs for a connection"""
        logs = [l for l in self._data if l["connection_id"] == connection_id]
        logs.sort(key=lambda x: x["created_at"], reverse=True)
        return logs[:limit]

    def get_stats(self, connection_id: str) -> Dict:
        """Get sync statistics"""
        logs = [l for l in self._data if l["connection_id"] == connection_id]
        return {
            "total": len(logs),
            "success": len([l for l in logs if l["status"] == "success"]),
            "failed": len([l for l in logs if l["status"] == "failed"]),
            "skipped": len([l for l in logs if l["status"] == "skipped"])
        }
