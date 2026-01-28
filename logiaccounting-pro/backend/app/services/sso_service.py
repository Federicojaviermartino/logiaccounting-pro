"""
Enterprise SSO Service

Handles SSO connections, authentication flows, and user provisioning.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
from app.utils.datetime_utils import utc_now
import os
import secrets

from app.models.store import db
from app.utils.encryption import encrypt_value, decrypt_value

from app.auth.sso.saml import SAMLProcessor, SAMLConfig, SAMLValidationError
from app.auth.sso.oauth import (
    OAuthProvider,
    OAuthError,
    MicrosoftOAuthProvider,
    GoogleOAuthProvider,
    OktaOAuthProvider,
    GitHubOAuthProvider,
)
from app.auth.sso.scim import SCIMProcessor, SCIMException


class SSOServiceError(Exception):
    """SSO service error"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code


class SSOService:
    """Enterprise SSO Service"""

    PROVIDER_CLASSES = {
        "microsoft": MicrosoftOAuthProvider,
        "google": GoogleOAuthProvider,
        "okta": OktaOAuthProvider,
        "github": GitHubOAuthProvider,
    }

    def __init__(self):
        self.base_url = os.getenv("BASE_URL", "https://logiaccounting-pro.onrender.com")

    # ===================
    # Connection Management
    # ===================

    def get_connections(self, filters: Dict = None) -> List[Dict]:
        """Get all SSO connections"""
        connections = db.sso_connections.find_all(filters)
        return [self._sanitize_connection(c) for c in connections]

    def get_connection(self, connection_id: str) -> Optional[Dict]:
        """Get single SSO connection"""
        connection = db.sso_connections.find_by_id(connection_id)
        if connection:
            return self._sanitize_connection(connection)
        return None

    def get_connection_by_domain(self, domain: str) -> Optional[Dict]:
        """Get SSO connection by email domain"""
        connection = db.sso_connections.find_by_domain(domain)
        if connection:
            return self._sanitize_connection(connection)
        return None

    def create_connection(self, data: Dict) -> Dict:
        """Create new SSO connection"""
        if data.get("client_secret"):
            data["client_secret_encrypted"] = encrypt_value(data.pop("client_secret"))

        if data.get("scim_token"):
            data["scim_token_encrypted"] = encrypt_value(data.pop("scim_token"))

        connection = db.sso_connections.create(data)
        return self._sanitize_connection(connection)

    def update_connection(self, connection_id: str, data: Dict) -> Optional[Dict]:
        """Update SSO connection"""
        if data.get("client_secret"):
            data["client_secret_encrypted"] = encrypt_value(data.pop("client_secret"))

        if data.get("scim_token"):
            data["scim_token_encrypted"] = encrypt_value(data.pop("scim_token"))

        connection = db.sso_connections.update(connection_id, data)
        if connection:
            return self._sanitize_connection(connection)
        return None

    def delete_connection(self, connection_id: str) -> bool:
        """Delete SSO connection"""
        return db.sso_connections.delete(connection_id)

    def _sanitize_connection(self, connection: Dict) -> Dict:
        """Remove sensitive data from connection"""
        sanitized = connection.copy()
        sanitized.pop("client_secret_encrypted", None)
        sanitized.pop("scim_token_encrypted", None)

        config = sanitized.get("configuration", {})
        config.pop("client_secret", None)
        config.pop("private_key", None)

        return sanitized

    # ===================
    # SAML Authentication
    # ===================

    def initiate_saml_login(self, connection_id: str, relay_state: str = None) -> Tuple[str, str]:
        """
        Initiate SAML authentication flow.
        Returns: (redirect_url, request_id)
        """
        connection = db.sso_connections.find_by_id(connection_id)
        if not connection:
            raise SSOServiceError("Connection not found", "connection_not_found")

        if connection.get("protocol") != "saml":
            raise SSOServiceError("Connection is not SAML", "invalid_protocol")

        if connection.get("status") != "active":
            raise SSOServiceError("Connection is not active", "connection_inactive")

        config = self._build_saml_config(connection)
        processor = SAMLProcessor(config)

        redirect_url, request_id = processor.create_authn_request(relay_state)

        db.sso_sessions.create({
            "connection_id": connection_id,
            "session_type": "saml",
            "state": request_id,
            "relay_state": relay_state,
            "status": "pending",
            "expires_at": (utc_now() + timedelta(minutes=10)).isoformat(),
        })

        return redirect_url, request_id

    def process_saml_response(
        self,
        connection_id: str,
        saml_response: str,
        relay_state: str = None,
    ) -> Dict[str, Any]:
        """
        Process SAML response and authenticate user.
        Returns: user data with session info
        """
        connection = db.sso_connections.find_by_id(connection_id)
        if not connection:
            raise SSOServiceError("Connection not found", "connection_not_found")

        config = self._build_saml_config(connection)
        processor = SAMLProcessor(config)

        try:
            user_info = processor.process_response(saml_response)
        except SAMLValidationError as e:
            db.scim_logs.create({
                "connection_id": connection_id,
                "operation": "saml_auth",
                "status": "error",
                "details": {"error": str(e)},
            })
            raise SSOServiceError(str(e), "saml_validation_error")

        return self._complete_sso_authentication(
            connection=connection,
            external_user_id=user_info.get("name_id"),
            email=user_info.get("email"),
            attributes=user_info.get("attributes", {}),
            protocol="saml",
        )

    def _build_saml_config(self, connection: Dict) -> SAMLConfig:
        """Build SAML configuration from connection data"""
        config = connection.get("configuration", {})

        return SAMLConfig.from_connection_data(
            entity_id=config.get("entity_id") or f"{self.base_url}/sso/saml/{connection['id']}/metadata",
            acs_url=f"{self.base_url}/api/v1/sso/saml/{connection['id']}/acs",
            sls_url=f"{self.base_url}/api/v1/sso/saml/{connection['id']}/sls",
            idp_entity_id=config.get("idp_entity_id"),
            idp_sso_url=config.get("idp_sso_url"),
            idp_slo_url=config.get("idp_slo_url"),
            idp_certificate=config.get("idp_certificate"),
            sp_certificate=config.get("sp_certificate"),
            sp_private_key=config.get("sp_private_key"),
        )

    # ===================
    # OAuth2/OIDC Authentication
    # ===================

    def initiate_oauth_login(
        self,
        connection_id: str,
        login_hint: str = None,
    ) -> Tuple[str, str]:
        """
        Initiate OAuth2/OIDC authentication flow.
        Returns: (authorization_url, state)
        """
        connection = db.sso_connections.find_by_id(connection_id)
        if not connection:
            raise SSOServiceError("Connection not found", "connection_not_found")

        if connection.get("protocol") not in ["oauth2", "oidc"]:
            raise SSOServiceError("Connection is not OAuth2/OIDC", "invalid_protocol")

        if connection.get("status") != "active":
            raise SSOServiceError("Connection is not active", "connection_inactive")

        provider = self._get_oauth_provider(connection)
        auth_url, state, nonce = provider.generate_authorization_url(login_hint=login_hint)

        db.sso_sessions.create({
            "connection_id": connection_id,
            "session_type": "oauth",
            "state": state,
            "nonce": nonce,
            "status": "pending",
            "expires_at": (utc_now() + timedelta(minutes=10)).isoformat(),
        })

        return auth_url, state

    async def process_oauth_callback(
        self,
        connection_id: str,
        code: str,
        state: str,
    ) -> Dict[str, Any]:
        """
        Process OAuth2/OIDC callback and authenticate user.
        Returns: user data with session info
        """
        connection = db.sso_connections.find_by_id(connection_id)
        if not connection:
            raise SSOServiceError("Connection not found", "connection_not_found")

        sso_session = db.sso_sessions.find_by_state(state)
        if not sso_session:
            raise SSOServiceError("Invalid state", "invalid_state")

        if sso_session.get("connection_id") != connection_id:
            raise SSOServiceError("State mismatch", "state_mismatch")

        provider = self._get_oauth_provider(connection)

        try:
            tokens = await provider.exchange_code(code, state)

            if tokens.id_token and connection.get("protocol") == "oidc":
                claims = provider.validate_id_token(
                    tokens.id_token,
                    nonce=sso_session.get("nonce"),
                )
                email = claims.get("email")
                external_user_id = claims.get("sub")
                attributes = claims
            else:
                user_info = await provider.get_user_info(tokens.access_token)
                email = user_info.email
                external_user_id = user_info.provider_user_id
                attributes = {
                    "first_name": user_info.first_name,
                    "last_name": user_info.last_name,
                    "display_name": user_info.display_name,
                    "groups": user_info.groups,
                    "raw": user_info.raw_attributes,
                }

        except OAuthError as e:
            db.scim_logs.create({
                "connection_id": connection_id,
                "operation": "oauth_auth",
                "status": "error",
                "details": {"error": str(e), "code": e.error_code},
            })
            raise SSOServiceError(str(e), e.error_code or "oauth_error")

        db.sso_sessions.update(sso_session["id"], {
            "status": "completed",
            "access_token_encrypted": encrypt_value(tokens.access_token) if tokens.access_token else None,
            "refresh_token_encrypted": encrypt_value(tokens.refresh_token) if tokens.refresh_token else None,
            "token_expires_at": (utc_now() + timedelta(seconds=tokens.expires_in)).isoformat() if tokens.expires_in else None,
        })

        return self._complete_sso_authentication(
            connection=connection,
            external_user_id=external_user_id,
            email=email,
            attributes=attributes,
            protocol=connection.get("protocol"),
        )

    def _get_oauth_provider(self, connection: Dict) -> OAuthProvider:
        """Get OAuth provider instance for connection"""
        provider_type = connection.get("provider_type", "").lower()
        config = connection.get("configuration", {})

        provider_class = self.PROVIDER_CLASSES.get(provider_type)
        if not provider_class:
            raise SSOServiceError(f"Unknown provider type: {provider_type}", "unknown_provider")

        client_secret = config.get("client_secret")
        if not client_secret and connection.get("client_secret_encrypted"):
            client_secret = decrypt_value(connection["client_secret_encrypted"])

        redirect_uri = f"{self.base_url}/api/v1/sso/oauth/{connection['id']}/callback"

        return provider_class(
            client_id=config.get("client_id", ""),
            client_secret=client_secret or "",
            redirect_uri=redirect_uri,
            scopes=config.get("scopes"),
            tenant_id=config.get("tenant_id"),
            domain=config.get("domain"),
        )

    # ===================
    # User Provisioning
    # ===================

    def _complete_sso_authentication(
        self,
        connection: Dict,
        external_user_id: str,
        email: str,
        attributes: Dict,
        protocol: str,
    ) -> Dict[str, Any]:
        """
        Complete SSO authentication by finding/creating user
        and linking external identity.
        """
        if not email:
            raise SSOServiceError("Email not provided by identity provider", "missing_email")

        external_identity = db.external_identities.find_by_external_id(
            connection["id"],
            external_user_id,
        )

        user = None
        if external_identity:
            user = db.users.find_by_id(external_identity.get("user_id"))

        if not user:
            user = db.users.find_by_email(email)

        jit_provisioning = connection.get("configuration", {}).get("jit_provisioning", True)

        if not user:
            if not jit_provisioning:
                raise SSOServiceError(
                    "User not found and JIT provisioning is disabled",
                    "user_not_provisioned"
                )

            user = self._create_user_from_sso(email, attributes, connection)

        if not external_identity:
            db.external_identities.create({
                "user_id": user["id"],
                "connection_id": connection["id"],
                "external_user_id": external_user_id,
                "external_email": email,
                "attributes": attributes,
            })
        else:
            db.external_identities.update(external_identity["id"], {
                "external_email": email,
                "attributes": attributes,
                "last_login_at": utc_now().isoformat(),
            })

        mapped_role = self._map_role(attributes.get("groups", []), connection)
        if mapped_role and mapped_role != user.get("role"):
            db.users.update(user["id"], {"role": mapped_role})
            user["role"] = mapped_role

        db.scim_logs.create({
            "connection_id": connection["id"],
            "operation": f"{protocol}_login",
            "status": "success",
            "details": {
                "user_id": user["id"],
                "email": email,
                "external_user_id": external_user_id,
            },
        })

        return {
            "user": {k: v for k, v in user.items() if k != "password"},
            "sso": {
                "connection_id": connection["id"],
                "connection_name": connection.get("name"),
                "provider": connection.get("provider_type"),
                "protocol": protocol,
            },
        }

    def _create_user_from_sso(
        self,
        email: str,
        attributes: Dict,
        connection: Dict,
    ) -> Dict:
        """Create new user from SSO attributes"""
        default_role = connection.get("configuration", {}).get("default_role", "client")

        user_data = {
            "email": email,
            "first_name": attributes.get("first_name") or attributes.get("given_name") or email.split("@")[0],
            "last_name": attributes.get("last_name") or attributes.get("family_name") or "",
            "role": default_role,
            "status": "active",
            "company_name": attributes.get("organization") or connection.get("name"),
            "password": "",
            "sso_only": True,
        }

        mapped_role = self._map_role(attributes.get("groups", []), connection)
        if mapped_role:
            user_data["role"] = mapped_role

        return db.users.create(user_data)

    def _map_role(self, groups: List[str], connection: Dict) -> Optional[str]:
        """Map IdP groups to application role"""
        if not groups:
            return None

        role_mapping = connection.get("configuration", {}).get("role_mapping", {})
        if not role_mapping:
            return None

        for group in groups:
            group_lower = group.lower()
            for idp_group, app_role in role_mapping.items():
                if idp_group.lower() in group_lower or group_lower in idp_group.lower():
                    return app_role

        return None

    # ===================
    # SCIM Provisioning
    # ===================

    def get_scim_processor(self, connection_id: str) -> SCIMProcessor:
        """Get SCIM processor for connection"""
        connection = db.sso_connections.find_by_id(connection_id)
        if not connection:
            raise SSOServiceError("Connection not found", "connection_not_found")

        if not connection.get("scim_enabled"):
            raise SSOServiceError("SCIM not enabled for connection", "scim_not_enabled")

        base_url = f"{self.base_url}/api/v1/scim/{connection_id}"
        return SCIMProcessor(base_url, connection_id)

    def validate_scim_token(self, connection_id: str, token: str) -> bool:
        """Validate SCIM bearer token"""
        connection = db.sso_connections.find_by_id(connection_id)
        if not connection:
            return False

        expected_token = connection.get("scim_token")
        if not expected_token and connection.get("scim_token_encrypted"):
            expected_token = decrypt_value(connection["scim_token_encrypted"])

        if not expected_token:
            return False

        if token.startswith("Bearer "):
            token = token[7:]

        return secrets.compare_digest(token, expected_token)

    def generate_scim_token(self, connection_id: str) -> str:
        """Generate new SCIM bearer token"""
        token = secrets.token_urlsafe(32)

        db.sso_connections.update(connection_id, {
            "scim_token_encrypted": encrypt_value(token),
            "scim_enabled": True,
        })

        return token

    # ===================
    # Domain Discovery
    # ===================

    def discover_connection(self, email: str) -> Optional[Dict]:
        """Discover SSO connection from email domain"""
        if "@" not in email:
            return None

        domain = email.split("@")[1].lower()
        connection = db.sso_connections.find_by_domain(domain)

        if connection and connection.get("status") == "active":
            return self._sanitize_connection(connection)

        return None


sso_service = SSOService()
