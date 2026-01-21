# LogiAccounting Pro - Phase 12 Tasks Part 1

## DATABASE MODELS & SAML 2.0 IMPLEMENTATION

---

## TASK 1: DATABASE MODELS

### 1.1 SSO Connection Model

**File:** `backend/app/models/sso_connection.py`

```python
"""
SSO Connection Model
Stores configuration for SAML, OAuth2, and OIDC connections
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.extensions import db
from app.utils.encryption import encrypt_value, decrypt_value
import uuid


class SSOConnection(db.Model):
    """SSO Connection configuration for an organization"""
    
    __tablename__ = 'sso_connections'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    
    # Basic info
    name = Column(String(255), nullable=False)
    protocol = Column(String(20), nullable=False)  # 'saml', 'oauth2', 'oidc'
    provider = Column(String(50), nullable=False)  # 'okta', 'azure_ad', 'google', 'custom'
    status = Column(String(20), default='inactive')  # 'active', 'inactive', 'testing'
    
    # SAML Configuration
    saml_entity_id = Column(String(500))
    saml_sso_url = Column(String(500))
    saml_slo_url = Column(String(500))
    saml_certificate = Column(Text)
    saml_sign_request = Column(Boolean, default=True)
    saml_want_assertions_signed = Column(Boolean, default=True)
    saml_name_id_format = Column(
        String(100), 
        default='urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'
    )
    
    # OAuth2 / OIDC Configuration
    oauth_client_id = Column(String(255))
    _oauth_client_secret = Column('oauth_client_secret_encrypted', Text)
    oauth_authorization_url = Column(String(500))
    oauth_token_url = Column(String(500))
    oauth_userinfo_url = Column(String(500))
    oauth_scopes = Column(Text, default='openid profile email')
    oidc_discovery_url = Column(String(500))
    oidc_jwks_uri = Column(String(500))
    
    # Attribute Mapping
    attribute_mapping = Column(JSON, default=lambda: {
        'email': 'email',
        'first_name': 'given_name',
        'last_name': 'family_name',
        'groups': 'groups'
    })
    
    # Role Mapping (IdP group -> app role)
    role_mapping = Column(JSON, default=dict)
    default_role = Column(String(50), default='client')
    
    # SCIM Configuration
    scim_enabled = Column(Boolean, default=False)
    _scim_token = Column('scim_token_encrypted', Text)
    scim_sync_groups = Column(Boolean, default=False)
    
    # Security Settings
    allowed_domains = Column(ARRAY(String), default=list)
    enforce_sso = Column(Boolean, default=False)
    allow_idp_initiated = Column(Boolean, default=True)
    session_duration_hours = Column(Integer, default=8)
    
    # Metadata
    metadata_url = Column(String(500))
    metadata_xml = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime)
    
    # Relationships
    organization = relationship('Organization', back_populates='sso_connections')
    sessions = relationship('SSOSession', back_populates='connection', cascade='all, delete-orphan')
    external_identities = relationship('UserExternalIdentity', back_populates='connection')
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'name', name='uq_sso_connection_org_name'),
    )
    
    # Properties for encrypted fields
    @property
    def oauth_client_secret(self) -> Optional[str]:
        if self._oauth_client_secret:
            return decrypt_value(self._oauth_client_secret)
        return None
    
    @oauth_client_secret.setter
    def oauth_client_secret(self, value: str):
        if value:
            self._oauth_client_secret = encrypt_value(value)
        else:
            self._oauth_client_secret = None
    
    @property
    def scim_token(self) -> Optional[str]:
        if self._scim_token:
            return decrypt_value(self._scim_token)
        return None
    
    @scim_token.setter
    def scim_token(self, value: str):
        if value:
            self._scim_token = encrypt_value(value)
        else:
            self._scim_token = None
    
    def get_sp_config(self) -> Dict[str, Any]:
        """Get Service Provider configuration for SAML"""
        from flask import current_app
        import os
        
        base_url = os.getenv('BASE_URL', 'https://logiaccounting-pro.onrender.com')
        
        return {
            'entityId': f"{base_url}/api/v1/auth/sso/saml/{self.id}/metadata",
            'assertionConsumerService': {
                'url': f"{base_url}/api/v1/auth/sso/saml/{self.id}/acs",
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            },
            'singleLogoutService': {
                'url': f"{base_url}/api/v1/auth/sso/saml/{self.id}/sls",
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            },
            'NameIDFormat': self.saml_name_id_format,
            'x509cert': os.getenv('SAML_SP_CERT', ''),
            'privateKey': os.getenv('SAML_SP_KEY', ''),
        }
    
    def get_idp_config(self) -> Dict[str, Any]:
        """Get Identity Provider configuration for SAML"""
        return {
            'entityId': self.saml_entity_id,
            'singleSignOnService': {
                'url': self.saml_sso_url,
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            },
            'singleLogoutService': {
                'url': self.saml_slo_url,
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            } if self.saml_slo_url else None,
            'x509cert': self.saml_certificate,
        }
    
    def get_scopes_list(self) -> List[str]:
        """Get OAuth scopes as list"""
        if self.oauth_scopes:
            return [s.strip() for s in self.oauth_scopes.split()]
        return ['openid', 'profile', 'email']
    
    def map_user_role(self, groups: List[str]) -> str:
        """Map IdP groups to application role"""
        if not self.role_mapping or not groups:
            return self.default_role
        
        for idp_group, app_role in self.role_mapping.items():
            if idp_group in groups:
                return app_role
        
        return self.default_role
    
    def is_domain_allowed(self, email: str) -> bool:
        """Check if email domain is allowed"""
        if not self.allowed_domains:
            return True
        
        domain = email.split('@')[1].lower() if '@' in email else ''
        return domain in [d.lower() for d in self.allowed_domains]
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'name': self.name,
            'protocol': self.protocol,
            'provider': self.provider,
            'status': self.status,
            'attribute_mapping': self.attribute_mapping,
            'role_mapping': self.role_mapping,
            'default_role': self.default_role,
            'allowed_domains': self.allowed_domains,
            'enforce_sso': self.enforce_sso,
            'allow_idp_initiated': self.allow_idp_initiated,
            'session_duration_hours': self.session_duration_hours,
            'scim_enabled': self.scim_enabled,
            'scim_sync_groups': self.scim_sync_groups,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
        }
        
        # Add protocol-specific fields
        if self.protocol == 'saml':
            data.update({
                'saml_entity_id': self.saml_entity_id,
                'saml_sso_url': self.saml_sso_url,
                'saml_slo_url': self.saml_slo_url,
                'saml_name_id_format': self.saml_name_id_format,
                'metadata_url': self.metadata_url,
            })
        elif self.protocol in ['oauth2', 'oidc']:
            data.update({
                'oauth_client_id': self.oauth_client_id,
                'oauth_authorization_url': self.oauth_authorization_url,
                'oauth_token_url': self.oauth_token_url,
                'oauth_userinfo_url': self.oauth_userinfo_url,
                'oauth_scopes': self.oauth_scopes,
                'oidc_discovery_url': self.oidc_discovery_url,
            })
        
        return data
    
    def __repr__(self):
        return f'<SSOConnection {self.name} ({self.protocol})>'
```

### 1.2 SSO Session Model

**File:** `backend/app/models/sso_session.py`

```python
"""
SSO Session Model
Tracks active SSO sessions for single logout support
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.extensions import db
from app.utils.encryption import encrypt_value, decrypt_value
import uuid


class SSOSession(db.Model):
    """SSO session for tracking IdP sessions"""
    
    __tablename__ = 'sso_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    connection_id = Column(UUID(as_uuid=True), db.ForeignKey('sso_connections.id'), nullable=False)
    
    # SAML session info
    session_index = Column(String(255))
    name_id = Column(String(255))
    name_id_format = Column(String(100))
    
    # OAuth tokens (encrypted)
    _access_token = Column('access_token_encrypted', Text)
    _refresh_token = Column('refresh_token_encrypted', Text)
    id_token = Column(Text)  # JWT - can be stored as-is
    token_expires_at = Column(DateTime)
    
    # Session state
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='sso_sessions')
    connection = relationship('SSOConnection', back_populates='sessions')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_sso_sessions_user', 'user_id'),
        db.Index('idx_sso_sessions_connection', 'connection_id'),
        db.Index('idx_sso_sessions_active', 'is_active', 'expires_at'),
    )
    
    @property
    def access_token(self) -> Optional[str]:
        if self._access_token:
            return decrypt_value(self._access_token)
        return None
    
    @access_token.setter
    def access_token(self, value: str):
        if value:
            self._access_token = encrypt_value(value)
        else:
            self._access_token = None
    
    @property
    def refresh_token(self) -> Optional[str]:
        if self._refresh_token:
            return decrypt_value(self._refresh_token)
        return None
    
    @refresh_token.setter
    def refresh_token(self, value: str):
        if value:
            self._refresh_token = encrypt_value(value)
        else:
            self._refresh_token = None
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_token_expired(self) -> bool:
        if not self.token_expires_at:
            return True
        return datetime.utcnow() > self.token_expires_at
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
        db.session.commit()
    
    def invalidate(self):
        """Invalidate the session"""
        self.is_active = False
        db.session.commit()
    
    @classmethod
    def create_session(
        cls,
        user_id: str,
        connection_id: str,
        duration_hours: int = 8,
        **kwargs
    ) -> 'SSOSession':
        """Create a new SSO session"""
        session = cls(
            user_id=user_id,
            connection_id=connection_id,
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours),
            **kwargs
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    @classmethod
    def get_active_session(cls, user_id: str, connection_id: str) -> Optional['SSOSession']:
        """Get active session for user and connection"""
        return cls.query.filter(
            cls.user_id == user_id,
            cls.connection_id == connection_id,
            cls.is_active == True,
            cls.expires_at > datetime.utcnow()
        ).first()
    
    @classmethod
    def invalidate_user_sessions(cls, user_id: str, connection_id: str = None):
        """Invalidate all sessions for a user"""
        query = cls.query.filter(cls.user_id == user_id, cls.is_active == True)
        
        if connection_id:
            query = query.filter(cls.connection_id == connection_id)
        
        query.update({'is_active': False})
        db.session.commit()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'connection_id': str(self.connection_id),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
        }


class UserExternalIdentity(db.Model):
    """Links users to external IdP identities"""
    
    __tablename__ = 'user_external_identities'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    connection_id = Column(UUID(as_uuid=True), db.ForeignKey('sso_connections.id'), nullable=False)
    
    # External identity
    external_id = Column(String(255), nullable=False)  # Subject/NameID from IdP
    provider_user_id = Column(String(255))  # Provider-specific user ID
    email = Column(String(255))
    
    # Profile data from IdP
    profile_data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Relationships
    user = relationship('User', back_populates='external_identities')
    connection = relationship('SSOConnection', back_populates='external_identities')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('connection_id', 'external_id', name='uq_external_identity'),
        db.Index('idx_external_identities_user', 'user_id'),
    )
    
    @classmethod
    def find_by_external_id(
        cls, 
        connection_id: str, 
        external_id: str
    ) -> Optional['UserExternalIdentity']:
        """Find identity by external ID"""
        return cls.query.filter(
            cls.connection_id == connection_id,
            cls.external_id == external_id
        ).first()
    
    @classmethod
    def find_or_create(
        cls,
        user_id: str,
        connection_id: str,
        external_id: str,
        **kwargs
    ) -> 'UserExternalIdentity':
        """Find existing or create new external identity"""
        identity = cls.find_by_external_id(connection_id, external_id)
        
        if not identity:
            identity = cls(
                user_id=user_id,
                connection_id=connection_id,
                external_id=external_id,
                **kwargs
            )
            db.session.add(identity)
        else:
            # Update existing
            for key, value in kwargs.items():
                if hasattr(identity, key):
                    setattr(identity, key, value)
        
        identity.last_login_at = datetime.utcnow()
        db.session.commit()
        
        return identity
```

### 1.3 SCIM Sync Log Model

**File:** `backend/app/models/scim_log.py`

```python
"""
SCIM Sync Log Model
Tracks SCIM provisioning operations
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.extensions import db
import uuid


class SCIMSyncLog(db.Model):
    """Log of SCIM provisioning operations"""
    
    __tablename__ = 'scim_sync_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), db.ForeignKey('sso_connections.id'), nullable=False)
    
    # Operation info
    operation = Column(String(20), nullable=False)  # 'create', 'update', 'delete', 'sync'
    resource_type = Column(String(20), nullable=False)  # 'user', 'group'
    external_id = Column(String(255))
    internal_id = Column(UUID(as_uuid=True))
    
    # Result
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'skipped'
    error_message = Column(Text)
    
    # Request/Response
    request_payload = Column(JSON)
    response_payload = Column(JSON)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_scim_logs_connection', 'connection_id'),
        db.Index('idx_scim_logs_created', 'created_at'),
        db.Index('idx_scim_logs_status', 'status'),
    )
    
    @classmethod
    def log_operation(
        cls,
        connection_id: str,
        operation: str,
        resource_type: str,
        status: str,
        external_id: str = None,
        internal_id: str = None,
        error_message: str = None,
        request_payload: Dict = None,
        response_payload: Dict = None
    ) -> 'SCIMSyncLog':
        """Create a new SCIM log entry"""
        log = cls(
            connection_id=connection_id,
            operation=operation,
            resource_type=resource_type,
            status=status,
            external_id=external_id,
            internal_id=internal_id,
            error_message=error_message,
            request_payload=request_payload,
            response_payload=response_payload
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @classmethod
    def get_recent_logs(
        cls, 
        connection_id: str, 
        limit: int = 100
    ) -> list:
        """Get recent logs for a connection"""
        return cls.query.filter(
            cls.connection_id == connection_id
        ).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'connection_id': str(self.connection_id),
            'operation': self.operation,
            'resource_type': self.resource_type,
            'external_id': self.external_id,
            'internal_id': str(self.internal_id) if self.internal_id else None,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
        }
```

### 1.4 Encryption Utilities

**File:** `backend/app/utils/encryption.py`

```python
"""
Encryption utilities for sensitive data
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_encryption_key() -> bytes:
    """Get or generate encryption key from environment"""
    key = os.getenv('ENCRYPTION_KEY')
    
    if not key:
        # For development only - generate from secret key
        secret = os.getenv('SECRET_KEY', 'dev-secret-key').encode()
        salt = os.getenv('ENCRYPTION_SALT', 'logiaccounting-salt').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret))
    else:
        key = key.encode() if isinstance(key, str) else key
    
    return key


def get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption"""
    return Fernet(get_encryption_key())


def encrypt_value(value: str) -> str:
    """Encrypt a string value"""
    if not value:
        return value
    
    f = get_fernet()
    encrypted = f.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt an encrypted string value"""
    if not encrypted_value:
        return encrypted_value
    
    f = get_fernet()
    decoded = base64.urlsafe_b64decode(encrypted_value.encode())
    decrypted = f.decrypt(decoded)
    return decrypted.decode()
```

---

## TASK 2: SAML 2.0 IMPLEMENTATION

### 2.1 SAML Configuration

**File:** `backend/app/auth/sso/saml/__init__.py`

```python
"""
SAML 2.0 Authentication Module
"""

from .config import SAMLConfig
from .processor import SAMLProcessor, SAMLValidationError
from .metadata import SAMLMetadataGenerator

__all__ = [
    'SAMLConfig',
    'SAMLProcessor',
    'SAMLValidationError',
    'SAMLMetadataGenerator',
]
```

**File:** `backend/app/auth/sso/saml/config.py`

```python
"""
SAML Configuration Management
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import os


@dataclass
class SAMLSecurityConfig:
    """Security settings for SAML"""
    
    # Signature settings
    authn_requests_signed: bool = True
    logout_requests_signed: bool = True
    logout_responses_signed: bool = True
    sign_metadata: bool = True
    
    # Validation settings
    want_messages_signed: bool = True
    want_assertions_signed: bool = True
    want_assertions_encrypted: bool = False
    want_name_id_encrypted: bool = False
    
    # Algorithm settings
    signature_algorithm: str = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
    digest_algorithm: str = "http://www.w3.org/2001/04/xmlenc#sha256"
    
    # Other settings
    reject_deprecated_algorithms: bool = True
    fail_on_authn_context_mismatch: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'authnRequestsSigned': self.authn_requests_signed,
            'logoutRequestSigned': self.logout_requests_signed,
            'logoutResponseSigned': self.logout_responses_signed,
            'signMetadata': self.sign_metadata,
            'wantMessagesSigned': self.want_messages_signed,
            'wantAssertionsSigned': self.want_assertions_signed,
            'wantAssertionsEncrypted': self.want_assertions_encrypted,
            'wantNameIdEncrypted': self.want_name_id_encrypted,
            'signatureAlgorithm': self.signature_algorithm,
            'digestAlgorithm': self.digest_algorithm,
            'rejectDeprecatedAlgorithm': self.reject_deprecated_algorithms,
            'failOnAuthnContextMismatch': self.fail_on_authn_context_mismatch,
            'requestedAuthnContext': False,
        }


@dataclass
class SAMLServiceProvider:
    """Service Provider configuration"""
    
    entity_id: str
    acs_url: str
    sls_url: str
    name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    x509_cert: str = ""
    private_key: str = ""
    
    # Organization info
    org_name: str = "LogiAccounting Pro"
    org_display_name: str = "LogiAccounting Pro"
    org_url: str = "https://logiaccounting-pro.onrender.com"
    
    # Contact info
    technical_contact_name: str = "Support"
    technical_contact_email: str = "support@logiaccounting.com"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entityId': self.entity_id,
            'assertionConsumerService': {
                'url': self.acs_url,
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            },
            'singleLogoutService': {
                'url': self.sls_url,
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            },
            'NameIDFormat': self.name_id_format,
            'x509cert': self.x509_cert,
            'privateKey': self.private_key,
        }


@dataclass
class SAMLIdentityProvider:
    """Identity Provider configuration"""
    
    entity_id: str
    sso_url: str
    slo_url: Optional[str] = None
    x509_cert: str = ""
    x509_cert_multi: List[str] = field(default_factory=list)
    sso_binding: str = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    slo_binding: str = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    
    def to_dict(self) -> Dict[str, Any]:
        config = {
            'entityId': self.entity_id,
            'singleSignOnService': {
                'url': self.sso_url,
                'binding': self.sso_binding,
            },
            'x509cert': self.x509_cert,
        }
        
        if self.slo_url:
            config['singleLogoutService'] = {
                'url': self.slo_url,
                'binding': self.slo_binding,
            }
        
        if self.x509_cert_multi:
            config['x509certMulti'] = {
                'signing': self.x509_cert_multi,
            }
        
        return config


class SAMLConfig:
    """Complete SAML configuration builder"""
    
    def __init__(
        self,
        connection_id: str,
        sp_config: Dict[str, Any],
        idp_config: Dict[str, Any],
        security_config: Optional[SAMLSecurityConfig] = None
    ):
        self.connection_id = connection_id
        self._sp = SAMLServiceProvider(**sp_config) if isinstance(sp_config, dict) else sp_config
        self._idp = SAMLIdentityProvider(**idp_config) if isinstance(idp_config, dict) else idp_config
        self._security = security_config or SAMLSecurityConfig()
    
    @classmethod
    def from_connection(cls, connection) -> 'SAMLConfig':
        """Build config from SSOConnection model"""
        base_url = os.getenv('BASE_URL', 'https://logiaccounting-pro.onrender.com')
        
        sp_config = {
            'entity_id': f"{base_url}/api/v1/auth/sso/saml/{connection.id}/metadata",
            'acs_url': f"{base_url}/api/v1/auth/sso/saml/{connection.id}/acs",
            'sls_url': f"{base_url}/api/v1/auth/sso/saml/{connection.id}/sls",
            'name_id_format': connection.saml_name_id_format,
            'x509_cert': os.getenv('SAML_SP_CERT', ''),
            'private_key': os.getenv('SAML_SP_KEY', ''),
        }
        
        idp_config = {
            'entity_id': connection.saml_entity_id,
            'sso_url': connection.saml_sso_url,
            'slo_url': connection.saml_slo_url,
            'x509_cert': connection.saml_certificate,
        }
        
        security = SAMLSecurityConfig(
            authn_requests_signed=connection.saml_sign_request,
            want_assertions_signed=connection.saml_want_assertions_signed,
        )
        
        return cls(
            connection_id=str(connection.id),
            sp_config=sp_config,
            idp_config=idp_config,
            security_config=security
        )
    
    def to_onelogin_settings(self) -> Dict[str, Any]:
        """Convert to python3-saml settings format"""
        return {
            'strict': True,
            'debug': os.getenv('SAML_DEBUG', 'false').lower() == 'true',
            'sp': self._sp.to_dict(),
            'idp': self._idp.to_dict(),
            'security': self._security.to_dict(),
        }
    
    @property
    def sp(self) -> SAMLServiceProvider:
        return self._sp
    
    @property
    def idp(self) -> SAMLIdentityProvider:
        return self._idp
    
    @property
    def security(self) -> SAMLSecurityConfig:
        return self._security
```

### 2.2 SAML Processor

**File:** `backend/app/auth/sso/saml/processor.py`

```python
"""
SAML Assertion Processor
Handles SAML authentication flow
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
import logging

from .config import SAMLConfig

logger = logging.getLogger(__name__)


class SAMLValidationError(Exception):
    """SAML validation error"""
    
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []


class SAMLProcessor:
    """Process SAML assertions and responses"""
    
    # Standard attribute URIs
    ATTRIBUTE_MAPPINGS = {
        # Email
        'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress': 'email',
        'http://schemas.xmlsoap.org/claims/EmailAddress': 'email',
        'email': 'email',
        'mail': 'email',
        'Email': 'email',
        
        # First Name
        'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname': 'first_name',
        'firstName': 'first_name',
        'givenName': 'first_name',
        'given_name': 'first_name',
        'FirstName': 'first_name',
        
        # Last Name
        'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname': 'last_name',
        'lastName': 'last_name',
        'sn': 'last_name',
        'family_name': 'last_name',
        'LastName': 'last_name',
        
        # Display Name
        'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name': 'display_name',
        'displayName': 'display_name',
        'name': 'display_name',
        'cn': 'display_name',
        
        # Groups
        'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups': 'groups',
        'http://schemas.xmlsoap.org/claims/Group': 'groups',
        'groups': 'groups',
        'memberOf': 'groups',
    }
    
    def __init__(self, config: SAMLConfig):
        self.config = config
        self.settings = config.to_onelogin_settings()
    
    def create_authn_request(
        self, 
        request_data: Dict[str, Any],
        return_to: str = '/'
    ) -> Tuple[str, str]:
        """
        Create SAML authentication request
        
        Args:
            request_data: Flask request data (prepared by prepare_request)
            return_to: URL to redirect after authentication
            
        Returns:
            Tuple of (redirect_url, request_id)
        """
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        
        # Generate redirect URL with embedded AuthnRequest
        redirect_url = auth.login(return_to=return_to)
        request_id = auth.get_last_request_id()
        
        logger.info(
            f"Created SAML AuthnRequest",
            extra={
                'request_id': request_id,
                'connection_id': self.config.connection_id,
                'return_to': return_to,
            }
        )
        
        return redirect_url, request_id
    
    def process_response(
        self, 
        request_data: Dict[str, Any],
        expected_request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process SAML response from IdP
        
        Args:
            request_data: Flask request data with SAMLResponse
            expected_request_id: Request ID to validate (InResponseTo)
            
        Returns:
            Dict with user attributes and session info
        """
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        
        # Process the SAML response
        auth.process_response(request_id=expected_request_id)
        
        # Check for errors
        errors = auth.get_errors()
        if errors:
            error_reason = auth.get_last_error_reason()
            logger.error(
                f"SAML Response validation failed",
                extra={
                    'errors': errors,
                    'reason': error_reason,
                    'connection_id': self.config.connection_id,
                }
            )
            raise SAMLValidationError(
                f"SAML validation failed: {error_reason}",
                errors=errors
            )
        
        # Verify authentication
        if not auth.is_authenticated():
            raise SAMLValidationError("User not authenticated in SAML response")
        
        # Extract session info
        name_id = auth.get_nameid()
        name_id_format = auth.get_nameid_format()
        session_index = auth.get_session_index()
        session_expiration = auth.get_session_expiration()
        
        # Extract and normalize attributes
        raw_attributes = auth.get_attributes()
        attributes = self._normalize_attributes(raw_attributes)
        
        # Use NameID as email if not in attributes
        if not attributes.get('email') and name_id:
            if '@' in name_id:
                attributes['email'] = name_id
        
        logger.info(
            f"SAML authentication successful",
            extra={
                'name_id': name_id,
                'session_index': session_index,
                'connection_id': self.config.connection_id,
            }
        )
        
        return {
            'name_id': name_id,
            'name_id_format': name_id_format,
            'session_index': session_index,
            'session_expiration': session_expiration,
            'attributes': attributes,
            'raw_attributes': raw_attributes,
        }
    
    def create_logout_request(
        self,
        request_data: Dict[str, Any],
        name_id: str,
        session_index: str,
        return_to: str = '/'
    ) -> str:
        """
        Create SAML logout request
        
        Returns:
            Redirect URL for logout
        """
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        
        redirect_url = auth.logout(
            name_id=name_id,
            session_index=session_index,
            return_to=return_to
        )
        
        logger.info(
            f"Created SAML LogoutRequest",
            extra={
                'name_id': name_id,
                'session_index': session_index,
                'connection_id': self.config.connection_id,
            }
        )
        
        return redirect_url
    
    def process_logout_response(
        self, 
        request_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Process SAML logout response or request
        
        Returns:
            Tuple of (success, redirect_url)
        """
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        
        # Determine if this is a request or response
        get_data = request_data.get('get_data', {})
        post_data = request_data.get('post_data', {})
        
        redirect_url = None
        
        if 'SAMLRequest' in get_data or 'SAMLRequest' in post_data:
            # IdP-initiated logout request
            redirect_url = auth.process_slo(
                keep_local_session=False,
                request_id=None,
                delete_session_cb=None
            )
        else:
            # SP-initiated logout response
            auth.process_slo()
        
        errors = auth.get_errors()
        if errors:
            logger.error(
                f"SAML Logout errors",
                extra={
                    'errors': errors,
                    'connection_id': self.config.connection_id,
                }
            )
            return False, redirect_url
        
        logger.info(
            f"SAML logout processed successfully",
            extra={'connection_id': self.config.connection_id}
        )
        
        return True, redirect_url
    
    def get_metadata(self) -> str:
        """Generate SP metadata XML"""
        from onelogin.saml2.metadata import OneLogin_Saml2_Metadata
        
        sp = self.settings['sp']
        security = self.settings['security']
        
        metadata = OneLogin_Saml2_Metadata.builder(
            sp=sp,
            authnsign=security.get('authnRequestsSigned', True),
            wsign=security.get('wantAssertionsSigned', True),
        )
        
        return metadata
    
    @classmethod
    def parse_idp_metadata(cls, metadata: str) -> Dict[str, Any]:
        """Parse IdP metadata XML and extract configuration"""
        parsed = OneLogin_Saml2_IdPMetadataParser.parse(metadata)
        
        idp = parsed.get('idp', {})
        
        return {
            'entity_id': idp.get('entityId', ''),
            'sso_url': idp.get('singleSignOnService', {}).get('url', ''),
            'slo_url': idp.get('singleLogoutService', {}).get('url'),
            'certificate': idp.get('x509cert', ''),
            'certificates': idp.get('x509certMulti', {}).get('signing', []),
        }
    
    @classmethod
    def parse_idp_metadata_url(cls, url: str) -> Dict[str, Any]:
        """Fetch and parse IdP metadata from URL"""
        import requests
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return cls.parse_idp_metadata(response.text)
    
    def _normalize_attributes(
        self, 
        attributes: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Normalize SAML attributes to standard format"""
        normalized = {}
        
        for attr_uri, values in attributes.items():
            # Get mapped key
            mapped_key = self.ATTRIBUTE_MAPPINGS.get(attr_uri, attr_uri)
            
            # Handle single vs multi-valued attributes
            if mapped_key in ['email', 'first_name', 'last_name', 'display_name']:
                # Single value
                normalized[mapped_key] = values[0] if values else None
            elif mapped_key == 'groups':
                # Multi-valued
                normalized[mapped_key] = values
            else:
                # Unknown attribute - keep as-is
                normalized[mapped_key] = values if len(values) > 1 else values[0] if values else None
        
        return normalized


def prepare_saml_request(flask_request) -> Dict[str, Any]:
    """
    Prepare Flask request data for python3-saml
    """
    url_data = flask_request.url.split('?')
    
    return {
        'https': 'on' if flask_request.scheme == 'https' else 'off',
        'http_host': flask_request.host,
        'server_port': flask_request.environ.get('SERVER_PORT', '443'),
        'script_name': flask_request.path,
        'get_data': flask_request.args.to_dict(),
        'post_data': flask_request.form.to_dict(),
        'query_string': flask_request.query_string.decode('utf-8'),
    }
```

### 2.3 SAML Metadata Generator

**File:** `backend/app/auth/sso/saml/metadata.py`

```python
"""
SAML Service Provider Metadata Generator
"""

from typing import Optional
from lxml import etree
from datetime import datetime, timedelta
import os


class SAMLMetadataGenerator:
    """Generate SAML SP Metadata XML"""
    
    SAML_NS = "urn:oasis:names:tc:SAML:2.0:metadata"
    DS_NS = "http://www.w3.org/2000/09/xmldsig#"
    
    NSMAP = {
        'md': SAML_NS,
        'ds': DS_NS,
    }
    
    def __init__(
        self,
        entity_id: str,
        acs_url: str,
        sls_url: str,
        certificate: str,
        name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        org_name: str = "LogiAccounting Pro",
        org_url: str = None,
        contact_email: str = None,
        want_assertions_signed: bool = True,
        authn_requests_signed: bool = True,
        valid_days: int = 365,
    ):
        self.entity_id = entity_id
        self.acs_url = acs_url
        self.sls_url = sls_url
        self.certificate = self._clean_certificate(certificate)
        self.name_id_format = name_id_format
        self.org_name = org_name
        self.org_url = org_url or os.getenv('BASE_URL', 'https://logiaccounting-pro.onrender.com')
        self.contact_email = contact_email or os.getenv('SUPPORT_EMAIL', 'support@logiaccounting.com')
        self.want_assertions_signed = want_assertions_signed
        self.authn_requests_signed = authn_requests_signed
        self.valid_days = valid_days
    
    def generate(self) -> str:
        """Generate metadata XML string"""
        root = self._build_metadata()
        return etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
    
    def _build_metadata(self) -> etree.Element:
        """Build metadata XML tree"""
        # Root element
        root = etree.Element(
            f"{{{self.SAML_NS}}}EntityDescriptor",
            nsmap=self.NSMAP
        )
        root.set('entityID', self.entity_id)
        root.set('validUntil', self._get_valid_until())
        
        # SPSSODescriptor
        sp_sso = etree.SubElement(
            root,
            f"{{{self.SAML_NS}}}SPSSODescriptor"
        )
        sp_sso.set('AuthnRequestsSigned', str(self.authn_requests_signed).lower())
        sp_sso.set('WantAssertionsSigned', str(self.want_assertions_signed).lower())
        sp_sso.set('protocolSupportEnumeration', 'urn:oasis:names:tc:SAML:2.0:protocol')
        
        # KeyDescriptor for signing
        if self.certificate:
            self._add_key_descriptor(sp_sso, 'signing')
            self._add_key_descriptor(sp_sso, 'encryption')
        
        # SingleLogoutService
        sls = etree.SubElement(
            sp_sso,
            f"{{{self.SAML_NS}}}SingleLogoutService"
        )
        sls.set('Binding', 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect')
        sls.set('Location', self.sls_url)
        
        # NameIDFormat
        name_id = etree.SubElement(
            sp_sso,
            f"{{{self.SAML_NS}}}NameIDFormat"
        )
        name_id.text = self.name_id_format
        
        # AssertionConsumerService
        acs = etree.SubElement(
            sp_sso,
            f"{{{self.SAML_NS}}}AssertionConsumerService"
        )
        acs.set('Binding', 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST')
        acs.set('Location', self.acs_url)
        acs.set('index', '0')
        acs.set('isDefault', 'true')
        
        # Organization
        org = etree.SubElement(root, f"{{{self.SAML_NS}}}Organization")
        
        org_name = etree.SubElement(org, f"{{{self.SAML_NS}}}OrganizationName")
        org_name.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
        org_name.text = self.org_name
        
        org_display = etree.SubElement(org, f"{{{self.SAML_NS}}}OrganizationDisplayName")
        org_display.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
        org_display.text = self.org_name
        
        org_url = etree.SubElement(org, f"{{{self.SAML_NS}}}OrganizationURL")
        org_url.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
        org_url.text = self.org_url
        
        # ContactPerson
        contact = etree.SubElement(root, f"{{{self.SAML_NS}}}ContactPerson")
        contact.set('contactType', 'technical')
        
        contact_email = etree.SubElement(contact, f"{{{self.SAML_NS}}}EmailAddress")
        contact_email.text = self.contact_email
        
        return root
    
    def _add_key_descriptor(self, parent: etree.Element, use: str):
        """Add KeyDescriptor element"""
        key_desc = etree.SubElement(
            parent,
            f"{{{self.SAML_NS}}}KeyDescriptor"
        )
        key_desc.set('use', use)
        
        key_info = etree.SubElement(key_desc, f"{{{self.DS_NS}}}KeyInfo")
        x509_data = etree.SubElement(key_info, f"{{{self.DS_NS}}}X509Data")
        x509_cert = etree.SubElement(x509_data, f"{{{self.DS_NS}}}X509Certificate")
        x509_cert.text = self.certificate
    
    def _clean_certificate(self, cert: str) -> str:
        """Remove PEM headers and whitespace from certificate"""
        if not cert:
            return ""
        
        return cert.replace(
            '-----BEGIN CERTIFICATE-----', ''
        ).replace(
            '-----END CERTIFICATE-----', ''
        ).replace('\n', '').replace('\r', '').strip()
    
    def _get_valid_until(self) -> str:
        """Get validity timestamp"""
        valid_until = datetime.utcnow() + timedelta(days=self.valid_days)
        return valid_until.strftime('%Y-%m-%dT%H:%M:%SZ')
```

---

## TASK 3: SAML ROUTES

**File:** `backend/app/routes/saml.py`

```python
"""
SAML Authentication Routes
"""

from flask import Blueprint, request, redirect, session, jsonify, Response
from app.auth.sso.saml import SAMLConfig, SAMLProcessor, SAMLValidationError
from app.auth.sso.saml.processor import prepare_saml_request
from app.auth.sso.saml.metadata import SAMLMetadataGenerator
from app.models.sso_connection import SSOConnection
from app.services.sso_service import SSOService
import logging
import os

logger = logging.getLogger(__name__)

saml_bp = Blueprint('saml', __name__, url_prefix='/api/v1/auth/sso/saml')


@saml_bp.route('/<connection_id>/login', methods=['GET'])
def saml_login(connection_id: str):
    """
    Initiate SAML login flow
    
    Redirects user to Identity Provider for authentication
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection or connection.protocol != 'saml':
        return jsonify({'error': 'Invalid SSO connection'}), 404
    
    if connection.status != 'active' and connection.status != 'testing':
        return jsonify({'error': 'SSO connection is not active'}), 403
    
    try:
        # Build SAML config
        config = SAMLConfig.from_connection(connection)
        processor = SAMLProcessor(config)
        
        # Prepare request
        request_data = prepare_saml_request(request)
        return_to = request.args.get('return_to', '/')
        
        # Create AuthnRequest
        redirect_url, request_id = processor.create_authn_request(
            request_data,
            return_to=return_to
        )
        
        # Store request ID for validation
        session['saml_request_id'] = request_id
        session['saml_connection_id'] = connection_id
        session['saml_return_to'] = return_to
        
        logger.info(f"SAML login initiated for connection {connection_id}")
        
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"SAML login error: {e}")
        return redirect(f'/login?error=saml_error&message={str(e)}')


@saml_bp.route('/<connection_id>/acs', methods=['POST'])
def saml_acs(connection_id: str):
    """
    SAML Assertion Consumer Service (ACS)
    
    Receives and processes SAML Response from IdP
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection:
        return redirect('/login?error=invalid_connection')
    
    try:
        # Build SAML config
        config = SAMLConfig.from_connection(connection)
        processor = SAMLProcessor(config)
        
        # Prepare request
        request_data = prepare_saml_request(request)
        
        # Get expected request ID
        expected_request_id = session.pop('saml_request_id', None)
        stored_connection_id = session.pop('saml_connection_id', None)
        return_to = session.pop('saml_return_to', '/')
        
        # Validate connection ID matches (for SP-initiated)
        if stored_connection_id and stored_connection_id != connection_id:
            if not connection.allow_idp_initiated:
                return redirect('/login?error=connection_mismatch')
        
        # Process SAML response
        result = processor.process_response(
            request_data,
            expected_request_id=expected_request_id if stored_connection_id else None
        )
        
        # Validate domain if restricted
        email = result['attributes'].get('email')
        if email and not connection.is_domain_allowed(email):
            return redirect('/login?error=domain_not_allowed')
        
        # Find or create user
        user = SSOService.find_or_create_user(
            connection=connection,
            attributes=result['attributes'],
            name_id=result['name_id'],
            session_index=result['session_index']
        )
        
        # Create application session
        tokens = SSOService.create_session(
            user=user,
            connection=connection,
            saml_data={
                'name_id': result['name_id'],
                'name_id_format': result['name_id_format'],
                'session_index': result['session_index'],
            }
        )
        
        # Update last used timestamp
        connection.last_used_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"SAML authentication successful for user {user.email}")
        
        # Redirect to frontend with tokens
        base_url = os.getenv('FRONTEND_URL', '')
        callback_url = f"{base_url}/auth/callback"
        
        return redirect(
            f"{callback_url}?token={tokens['access_token']}"
            f"&refresh={tokens['refresh_token']}"
            f"&return_to={return_to}"
        )
        
    except SAMLValidationError as e:
        logger.error(f"SAML validation error: {e}")
        return redirect(f'/login?error=saml_validation&message={str(e)}')
    except Exception as e:
        logger.exception(f"SAML ACS error: {e}")
        return redirect(f'/login?error=saml_error&message={str(e)}')


@saml_bp.route('/<connection_id>/sls', methods=['GET', 'POST'])
def saml_sls(connection_id: str):
    """
    SAML Single Logout Service (SLS)
    
    Handles logout requests from IdP and logout responses
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection:
        return redirect('/login')
    
    try:
        config = SAMLConfig.from_connection(connection)
        processor = SAMLProcessor(config)
        
        request_data = prepare_saml_request(request)
        
        success, redirect_url = processor.process_logout_response(request_data)
        
        if success:
            # Invalidate local sessions
            SSOService.logout_user_sso(connection_id)
            logger.info(f"SAML logout successful for connection {connection_id}")
        
        return redirect(redirect_url or '/login?logout=success')
        
    except Exception as e:
        logger.error(f"SAML SLS error: {e}")
        return redirect('/login?logout=error')


@saml_bp.route('/<connection_id>/logout', methods=['POST'])
def saml_logout(connection_id: str):
    """
    Initiate SAML logout (SP-initiated)
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection or not connection.saml_slo_url:
        # No SLO configured, just logout locally
        SSOService.logout_user_sso(connection_id)
        return jsonify({'success': True, 'redirect': '/login'})
    
    try:
        # Get current user's SSO session
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        
        sso_session = SSOSession.get_active_session(user_id, connection_id)
        if not sso_session:
            return jsonify({'success': True, 'redirect': '/login'})
        
        config = SAMLConfig.from_connection(connection)
        processor = SAMLProcessor(config)
        
        request_data = prepare_saml_request(request)
        
        redirect_url = processor.create_logout_request(
            request_data,
            name_id=sso_session.name_id,
            session_index=sso_session.session_index,
            return_to='/login'
        )
        
        return jsonify({'success': True, 'redirect': redirect_url})
        
    except Exception as e:
        logger.error(f"SAML logout error: {e}")
        SSOService.logout_user_sso(connection_id)
        return jsonify({'success': True, 'redirect': '/login'})


@saml_bp.route('/<connection_id>/metadata', methods=['GET'])
def saml_metadata(connection_id: str):
    """
    Get SP metadata for IdP configuration
    
    Returns XML metadata that can be imported into IdP
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection:
        return jsonify({'error': 'Invalid connection'}), 404
    
    base_url = os.getenv('BASE_URL', 'https://logiaccounting-pro.onrender.com')
    
    generator = SAMLMetadataGenerator(
        entity_id=f"{base_url}/api/v1/auth/sso/saml/{connection_id}/metadata",
        acs_url=f"{base_url}/api/v1/auth/sso/saml/{connection_id}/acs",
        sls_url=f"{base_url}/api/v1/auth/sso/saml/{connection_id}/sls",
        certificate=os.getenv('SAML_SP_CERT', ''),
        name_id_format=connection.saml_name_id_format,
        want_assertions_signed=connection.saml_want_assertions_signed,
        authn_requests_signed=connection.saml_sign_request,
    )
    
    metadata = generator.generate()
    
    return Response(
        metadata,
        mimetype='application/xml',
        headers={
            'Content-Disposition': f'attachment; filename="sp-metadata-{connection_id}.xml"'
        }
    )


@saml_bp.route('/<connection_id>/parse-metadata', methods=['POST'])
def parse_idp_metadata(connection_id: str):
    """
    Parse IdP metadata (URL or XML)
    
    Helper endpoint for configuring SSO connection
    """
    data = request.get_json()
    
    try:
        if data.get('metadata_url'):
            parsed = SAMLProcessor.parse_idp_metadata_url(data['metadata_url'])
        elif data.get('metadata_xml'):
            parsed = SAMLProcessor.parse_idp_metadata(data['metadata_xml'])
        else:
            return jsonify({'error': 'Provide metadata_url or metadata_xml'}), 400
        
        return jsonify({
            'success': True,
            'parsed': parsed
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
```

---

## Continue to Part 2 for OAuth2/OIDC Implementation

---

*Phase 12 Tasks Part 1 - LogiAccounting Pro*
*Database Models and SAML 2.0 Implementation*
