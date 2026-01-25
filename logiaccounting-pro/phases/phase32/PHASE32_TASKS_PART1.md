# Phase 32: Advanced Security - Part 1: Security Config & MFA

## Overview
This part covers security configuration and Multi-Factor Authentication (MFA) implementation.

---

## File 1: Security Configuration
**Path:** `backend/app/security/config.py`

```python
"""
Security Configuration
Central configuration for all security features
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import os
from datetime import timedelta


class SecurityLevel(str, Enum):
    """Security level presets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ENTERPRISE = "enterprise"


@dataclass
class PasswordPolicy:
    """Password requirements."""
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    max_age_days: int = 90
    history_count: int = 5  # Cannot reuse last N passwords
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30


@dataclass
class SessionPolicy:
    """Session management settings."""
    max_concurrent_sessions: int = 5
    session_timeout_minutes: int = 60
    idle_timeout_minutes: int = 30
    absolute_timeout_hours: int = 24
    require_reauthentication_for_sensitive: bool = True
    track_devices: bool = True


@dataclass
class MFAPolicy:
    """MFA settings."""
    required: bool = False
    required_for_admins: bool = True
    allowed_methods: List[str] = field(default_factory=lambda: ["totp", "email"])
    backup_codes_count: int = 10
    totp_issuer: str = "LogiAccounting Pro"
    totp_algorithm: str = "SHA1"
    totp_digits: int = 6
    totp_period: int = 30  # seconds


@dataclass
class RateLimitPolicy:
    """Rate limiting settings."""
    enabled: bool = True
    default_requests_per_minute: int = 60
    login_attempts_per_minute: int = 5
    api_requests_per_minute: int = 100
    file_uploads_per_hour: int = 50
    burst_multiplier: float = 1.5


@dataclass
class EncryptionPolicy:
    """Encryption settings."""
    algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    encrypt_pii: bool = True
    encrypt_financial: bool = True
    field_level_encryption: bool = True


@dataclass
class AuditPolicy:
    """Audit logging settings."""
    enabled: bool = True
    log_auth_events: bool = True
    log_data_access: bool = True
    log_data_modifications: bool = True
    log_admin_actions: bool = True
    retention_days: int = 365
    immutable: bool = True


@dataclass
class SecurityConfig:
    """Main security configuration."""
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    # Secrets
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "change-me-in-production"))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "change-me-in-production"))
    encryption_key: str = field(default_factory=lambda: os.getenv("ENCRYPTION_KEY", ""))
    
    # JWT Settings
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Policies
    password_policy: PasswordPolicy = field(default_factory=PasswordPolicy)
    session_policy: SessionPolicy = field(default_factory=SessionPolicy)
    mfa_policy: MFAPolicy = field(default_factory=MFAPolicy)
    rate_limit_policy: RateLimitPolicy = field(default_factory=RateLimitPolicy)
    encryption_policy: EncryptionPolicy = field(default_factory=EncryptionPolicy)
    audit_policy: AuditPolicy = field(default_factory=AuditPolicy)
    
    # Security headers
    enable_hsts: bool = True
    hsts_max_age: int = 31536000  # 1 year
    enable_csp: bool = True
    enable_cors: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:5173"])
    
    # IP Security
    enable_ip_filtering: bool = True
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    geo_blocking_enabled: bool = False
    blocked_countries: List[str] = field(default_factory=list)
    
    # OAuth Providers
    oauth_providers: Dict[str, Dict] = field(default_factory=dict)
    
    def __post_init__(self):
        """Load OAuth providers from environment."""
        # Google OAuth
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if google_client_id and google_client_secret:
            self.oauth_providers["google"] = {
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "authorize_url": "https://accounts.google.com/o/oauth2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile",
            }
        
        # Microsoft OAuth
        ms_client_id = os.getenv("MICROSOFT_CLIENT_ID")
        ms_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        if ms_client_id and ms_client_secret:
            self.oauth_providers["microsoft"] = {
                "client_id": ms_client_id,
                "client_secret": ms_client_secret,
                "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me",
                "scope": "openid email profile User.Read",
            }
    
    @classmethod
    def from_level(cls, level: SecurityLevel) -> "SecurityConfig":
        """Create config from security level preset."""
        config = cls()
        
        if level == SecurityLevel.LOW:
            config.password_policy.min_length = 8
            config.password_policy.require_special = False
            config.mfa_policy.required = False
            config.mfa_policy.required_for_admins = False
            config.session_policy.session_timeout_minutes = 120
            
        elif level == SecurityLevel.MEDIUM:
            config.password_policy.min_length = 10
            config.mfa_policy.required = False
            config.mfa_policy.required_for_admins = True
            
        elif level == SecurityLevel.HIGH:
            config.password_policy.min_length = 12
            config.mfa_policy.required = True
            config.session_policy.session_timeout_minutes = 30
            config.rate_limit_policy.login_attempts_per_minute = 3
            
        elif level == SecurityLevel.ENTERPRISE:
            config.password_policy.min_length = 14
            config.password_policy.max_age_days = 60
            config.mfa_policy.required = True
            config.mfa_policy.allowed_methods = ["totp"]
            config.session_policy.max_concurrent_sessions = 3
            config.session_policy.session_timeout_minutes = 15
            config.rate_limit_policy.login_attempts_per_minute = 3
            config.encryption_policy.key_rotation_days = 30
            config.audit_policy.retention_days = 730  # 2 years
        
        return config
    
    def validate(self) -> List[str]:
        """Validate configuration and return warnings."""
        warnings = []
        
        if self.secret_key == "change-me-in-production":
            warnings.append("Using default SECRET_KEY - change in production")
        
        if self.jwt_secret == "change-me-in-production":
            warnings.append("Using default JWT_SECRET - change in production")
        
        if not self.encryption_key:
            warnings.append("ENCRYPTION_KEY not set - field encryption disabled")
        
        if self.debug and self.environment == "production":
            warnings.append("Debug mode enabled in production")
        
        if not self.enable_hsts and self.environment == "production":
            warnings.append("HSTS disabled in production")
        
        return warnings


# Global security configuration
security_config = SecurityConfig()


def get_security_config() -> SecurityConfig:
    """Get global security configuration."""
    return security_config


def configure_security(level: SecurityLevel = None, **kwargs) -> SecurityConfig:
    """Configure security settings."""
    global security_config
    
    if level:
        security_config = SecurityConfig.from_level(level)
    
    # Apply overrides
    for key, value in kwargs.items():
        if hasattr(security_config, key):
            setattr(security_config, key, value)
    
    return security_config
```

---

## File 2: MFA Core
**Path:** `backend/app/security/auth/mfa.py`

```python
"""
Multi-Factor Authentication
TOTP, SMS, and Email verification
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib
import base64
import logging
from uuid import uuid4

import pyotp
from cryptography.fernet import Fernet

from app.security.config import get_security_config

logger = logging.getLogger(__name__)


class MFAMethod(str, Enum):
    """Available MFA methods."""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODE = "backup_code"


@dataclass
class MFASetup:
    """MFA setup information."""
    method: MFAMethod
    secret: Optional[str] = None
    qr_code_uri: Optional[str] = None
    backup_codes: List[str] = field(default_factory=list)
    phone_number: Optional[str] = None
    email: Optional[str] = None


@dataclass
class MFAVerification:
    """MFA verification result."""
    success: bool
    method: MFAMethod
    message: str = ""
    remaining_attempts: int = 3


class MFAManager:
    """Manages multi-factor authentication."""
    
    MAX_VERIFICATION_ATTEMPTS = 3
    VERIFICATION_WINDOW = 1  # TOTP windows (30 seconds each)
    CODE_EXPIRY_MINUTES = 10
    
    def __init__(self):
        self.config = get_security_config().mfa_policy
        self._pending_verifications: Dict[str, Dict] = {}
        self._attempt_counts: Dict[str, int] = {}
    
    def setup_totp(self, user_id: str, email: str) -> MFASetup:
        """Setup TOTP for a user."""
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP object
        totp = pyotp.TOTP(
            secret,
            issuer=self.config.totp_issuer,
            digits=self.config.totp_digits,
            interval=self.config.totp_period,
        )
        
        # Generate provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name=self.config.totp_issuer,
        )
        
        # Generate backup codes
        backup_codes = self._generate_backup_codes()
        
        logger.info(f"TOTP setup initiated for user {user_id}")
        
        return MFASetup(
            method=MFAMethod.TOTP,
            secret=secret,
            qr_code_uri=provisioning_uri,
            backup_codes=backup_codes,
        )
    
    def verify_totp(self, secret: str, code: str) -> MFAVerification:
        """Verify TOTP code."""
        totp = pyotp.TOTP(
            secret,
            digits=self.config.totp_digits,
            interval=self.config.totp_period,
        )
        
        # Verify with window for clock drift
        is_valid = totp.verify(code, valid_window=self.VERIFICATION_WINDOW)
        
        return MFAVerification(
            success=is_valid,
            method=MFAMethod.TOTP,
            message="Code verified" if is_valid else "Invalid code",
        )
    
    def setup_sms(self, user_id: str, phone_number: str) -> MFASetup:
        """Setup SMS verification."""
        # Normalize phone number
        normalized_phone = self._normalize_phone(phone_number)
        
        logger.info(f"SMS MFA setup for user {user_id}")
        
        return MFASetup(
            method=MFAMethod.SMS,
            phone_number=normalized_phone,
            backup_codes=self._generate_backup_codes(),
        )
    
    def send_sms_code(self, user_id: str, phone_number: str) -> str:
        """Send SMS verification code."""
        code = self._generate_numeric_code(6)
        
        # Store pending verification
        self._pending_verifications[f"sms_{user_id}"] = {
            "code": code,
            "phone": phone_number,
            "expires_at": datetime.utcnow() + timedelta(minutes=self.CODE_EXPIRY_MINUTES),
            "attempts": 0,
        }
        
        # In production, integrate with SMS provider (Twilio, etc.)
        # For now, log the code (development only)
        if get_security_config().debug:
            logger.debug(f"SMS code for {user_id}: {code}")
        
        # TODO: Integrate SMS provider
        # sms_provider.send(phone_number, f"Your verification code is: {code}")
        
        return code  # Remove in production
    
    def verify_sms_code(self, user_id: str, code: str) -> MFAVerification:
        """Verify SMS code."""
        key = f"sms_{user_id}"
        pending = self._pending_verifications.get(key)
        
        if not pending:
            return MFAVerification(
                success=False,
                method=MFAMethod.SMS,
                message="No pending verification",
            )
        
        # Check expiry
        if datetime.utcnow() > pending["expires_at"]:
            del self._pending_verifications[key]
            return MFAVerification(
                success=False,
                method=MFAMethod.SMS,
                message="Code expired",
            )
        
        # Check attempts
        pending["attempts"] += 1
        if pending["attempts"] > self.MAX_VERIFICATION_ATTEMPTS:
            del self._pending_verifications[key]
            return MFAVerification(
                success=False,
                method=MFAMethod.SMS,
                message="Too many attempts",
                remaining_attempts=0,
            )
        
        # Verify code
        if secrets.compare_digest(pending["code"], code):
            del self._pending_verifications[key]
            return MFAVerification(
                success=True,
                method=MFAMethod.SMS,
                message="Code verified",
            )
        
        return MFAVerification(
            success=False,
            method=MFAMethod.SMS,
            message="Invalid code",
            remaining_attempts=self.MAX_VERIFICATION_ATTEMPTS - pending["attempts"],
        )
    
    def setup_email(self, user_id: str, email: str) -> MFASetup:
        """Setup email verification."""
        logger.info(f"Email MFA setup for user {user_id}")
        
        return MFASetup(
            method=MFAMethod.EMAIL,
            email=email,
            backup_codes=self._generate_backup_codes(),
        )
    
    def send_email_code(self, user_id: str, email: str) -> str:
        """Send email verification code."""
        code = self._generate_numeric_code(6)
        
        self._pending_verifications[f"email_{user_id}"] = {
            "code": code,
            "email": email,
            "expires_at": datetime.utcnow() + timedelta(minutes=self.CODE_EXPIRY_MINUTES),
            "attempts": 0,
        }
        
        # In production, send actual email
        if get_security_config().debug:
            logger.debug(f"Email code for {user_id}: {code}")
        
        # TODO: Integrate email service
        # email_service.send(email, "Verification Code", f"Your code is: {code}")
        
        return code  # Remove in production
    
    def verify_email_code(self, user_id: str, code: str) -> MFAVerification:
        """Verify email code."""
        key = f"email_{user_id}"
        pending = self._pending_verifications.get(key)
        
        if not pending:
            return MFAVerification(
                success=False,
                method=MFAMethod.EMAIL,
                message="No pending verification",
            )
        
        if datetime.utcnow() > pending["expires_at"]:
            del self._pending_verifications[key]
            return MFAVerification(
                success=False,
                method=MFAMethod.EMAIL,
                message="Code expired",
            )
        
        pending["attempts"] += 1
        if pending["attempts"] > self.MAX_VERIFICATION_ATTEMPTS:
            del self._pending_verifications[key]
            return MFAVerification(
                success=False,
                method=MFAMethod.EMAIL,
                message="Too many attempts",
                remaining_attempts=0,
            )
        
        if secrets.compare_digest(pending["code"], code):
            del self._pending_verifications[key]
            return MFAVerification(
                success=True,
                method=MFAMethod.EMAIL,
                message="Code verified",
            )
        
        return MFAVerification(
            success=False,
            method=MFAMethod.EMAIL,
            message="Invalid code",
            remaining_attempts=self.MAX_VERIFICATION_ATTEMPTS - pending["attempts"],
        )
    
    def verify_backup_code(
        self,
        code: str,
        hashed_codes: List[str],
    ) -> Tuple[bool, Optional[str]]:
        """Verify backup code and return the used hash to remove."""
        code_hash = self._hash_backup_code(code)
        
        for stored_hash in hashed_codes:
            if secrets.compare_digest(code_hash, stored_hash):
                return True, stored_hash
        
        return False, None
    
    def _generate_backup_codes(self) -> List[str]:
        """Generate backup codes."""
        count = self.config.backup_codes_count
        codes = []
        
        for _ in range(count):
            # Format: XXXX-XXXX-XXXX
            code = "-".join([
                secrets.token_hex(2).upper()
                for _ in range(3)
            ])
            codes.append(code)
        
        return codes
    
    def hash_backup_codes(self, codes: List[str]) -> List[str]:
        """Hash backup codes for storage."""
        return [self._hash_backup_code(code) for code in codes]
    
    def _hash_backup_code(self, code: str) -> str:
        """Hash a single backup code."""
        # Remove dashes for comparison
        normalized = code.replace("-", "").upper()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def _generate_numeric_code(self, length: int = 6) -> str:
        """Generate numeric verification code."""
        return "".join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number."""
        # Remove non-digits
        digits = "".join(filter(str.isdigit, phone))
        
        # Add country code if missing (assume US)
        if len(digits) == 10:
            digits = "1" + digits
        
        return f"+{digits}"


# Global MFA manager
mfa_manager = MFAManager()


def get_mfa_manager() -> MFAManager:
    """Get MFA manager instance."""
    return mfa_manager
```

---

## File 3: MFA Models
**Path:** `backend/app/security/auth/mfa_models.py`

```python
"""
MFA Database Models
SQLAlchemy models for MFA data
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class MFASettings(Base):
    """User MFA settings."""
    
    __tablename__ = "mfa_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # MFA method
    method = Column(String(20), nullable=False)  # 'totp', 'sms', 'email'
    
    # TOTP secret (encrypted)
    totp_secret_encrypted = Column(Text, nullable=True)
    
    # SMS phone number (encrypted)
    phone_number_encrypted = Column(String(255), nullable=True)
    
    # Email for verification (if different from user email)
    verification_email = Column(String(255), nullable=True)
    
    # Status
    is_enabled = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Backup codes (hashed)
    backup_codes_hash = Column(JSON, default=list)
    backup_codes_remaining = Column(Integer, default=10)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mfa_settings")
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "method": self.method,
            "is_enabled": self.is_enabled,
            "is_verified": self.is_verified,
            "backup_codes_remaining": self.backup_codes_remaining,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


class MFARecoveryCode(Base):
    """MFA recovery/backup codes."""
    
    __tablename__ = "mfa_recovery_codes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Code hash
    code_hash = Column(String(64), nullable=False)
    
    # Status
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class MFAChallenge(Base):
    """Pending MFA challenges."""
    
    __tablename__ = "mfa_challenges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Challenge type
    method = Column(String(20), nullable=False)
    
    # Challenge data (encrypted code for SMS/email)
    challenge_data_encrypted = Column(Text, nullable=True)
    
    # Status
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
```

---

## File 4: MFA Service
**Path:** `backend/app/security/auth/mfa_service.py`

```python
"""
MFA Service
High-level service for MFA operations
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.security.auth.mfa import MFAManager, MFAMethod, MFASetup, MFAVerification, mfa_manager
from app.security.auth.mfa_models import MFASettings, MFAChallenge
from app.security.encryption.fields import encrypt_field, decrypt_field

logger = logging.getLogger(__name__)


class MFAService:
    """Service for MFA operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.mfa = mfa_manager
    
    async def setup_mfa(
        self,
        user_id: str,
        method: str,
        email: str = None,
        phone: str = None,
    ) -> Dict[str, Any]:
        """Setup MFA for a user."""
        method_enum = MFAMethod(method)
        
        # Check if MFA already exists
        existing = self.db.query(MFASettings).filter(
            MFASettings.user_id == user_id
        ).first()
        
        if existing and existing.is_enabled:
            return {
                "success": False,
                "error": "MFA already enabled. Disable first to change method.",
            }
        
        # Setup based on method
        if method_enum == MFAMethod.TOTP:
            setup = self.mfa.setup_totp(user_id, email)
        elif method_enum == MFAMethod.SMS:
            if not phone:
                return {"success": False, "error": "Phone number required for SMS MFA"}
            setup = self.mfa.setup_sms(user_id, phone)
        elif method_enum == MFAMethod.EMAIL:
            setup = self.mfa.setup_email(user_id, email)
        else:
            return {"success": False, "error": f"Unsupported MFA method: {method}"}
        
        # Store settings (not enabled until verified)
        if existing:
            mfa_settings = existing
        else:
            mfa_settings = MFASettings(user_id=user_id)
        
        mfa_settings.method = method
        mfa_settings.is_enabled = False
        mfa_settings.is_verified = False
        
        # Encrypt and store sensitive data
        if setup.secret:
            mfa_settings.totp_secret_encrypted = encrypt_field(setup.secret)
        
        if setup.phone_number:
            mfa_settings.phone_number_encrypted = encrypt_field(setup.phone_number)
        
        # Hash and store backup codes
        if setup.backup_codes:
            mfa_settings.backup_codes_hash = self.mfa.hash_backup_codes(setup.backup_codes)
            mfa_settings.backup_codes_remaining = len(setup.backup_codes)
        
        self.db.add(mfa_settings)
        self.db.commit()
        
        logger.info(f"MFA setup initiated for user {user_id} using {method}")
        
        return {
            "success": True,
            "method": method,
            "qr_code_uri": setup.qr_code_uri,
            "backup_codes": setup.backup_codes,  # Show once during setup
            "requires_verification": True,
        }
    
    async def verify_setup(self, user_id: str, code: str) -> Dict[str, Any]:
        """Verify MFA setup with code."""
        mfa_settings = self.db.query(MFASettings).filter(
            MFASettings.user_id == user_id
        ).first()
        
        if not mfa_settings:
            return {"success": False, "error": "MFA not configured"}
        
        if mfa_settings.is_verified:
            return {"success": False, "error": "MFA already verified"}
        
        # Verify based on method
        method = MFAMethod(mfa_settings.method)
        
        if method == MFAMethod.TOTP:
            secret = decrypt_field(mfa_settings.totp_secret_encrypted)
            result = self.mfa.verify_totp(secret, code)
        elif method == MFAMethod.SMS:
            result = self.mfa.verify_sms_code(user_id, code)
        elif method == MFAMethod.EMAIL:
            result = self.mfa.verify_email_code(user_id, code)
        else:
            return {"success": False, "error": "Unknown MFA method"}
        
        if result.success:
            mfa_settings.is_verified = True
            mfa_settings.is_enabled = True
            mfa_settings.verified_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"MFA enabled for user {user_id}")
            
            return {
                "success": True,
                "message": "MFA enabled successfully",
            }
        
        return {
            "success": False,
            "error": result.message,
            "remaining_attempts": result.remaining_attempts,
        }
    
    async def verify_code(self, user_id: str, code: str) -> Dict[str, Any]:
        """Verify MFA code during login."""
        mfa_settings = self.db.query(MFASettings).filter(
            MFASettings.user_id == user_id,
            MFASettings.is_enabled == True,
        ).first()
        
        if not mfa_settings:
            return {"success": False, "error": "MFA not enabled"}
        
        method = MFAMethod(mfa_settings.method)
        
        # First check if it's a backup code
        is_backup, used_hash = self.mfa.verify_backup_code(
            code,
            mfa_settings.backup_codes_hash,
        )
        
        if is_backup:
            # Remove used backup code
            mfa_settings.backup_codes_hash.remove(used_hash)
            mfa_settings.backup_codes_remaining -= 1
            mfa_settings.last_used_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Backup code used for user {user_id}")
            
            return {
                "success": True,
                "method": "backup_code",
                "backup_codes_remaining": mfa_settings.backup_codes_remaining,
            }
        
        # Verify with primary method
        if method == MFAMethod.TOTP:
            secret = decrypt_field(mfa_settings.totp_secret_encrypted)
            result = self.mfa.verify_totp(secret, code)
        elif method == MFAMethod.SMS:
            result = self.mfa.verify_sms_code(user_id, code)
        elif method == MFAMethod.EMAIL:
            result = self.mfa.verify_email_code(user_id, code)
        else:
            return {"success": False, "error": "Unknown method"}
        
        if result.success:
            mfa_settings.last_used_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "success": True,
                "method": method.value,
            }
        
        return {
            "success": False,
            "error": result.message,
            "remaining_attempts": result.remaining_attempts,
        }
    
    async def send_verification_code(self, user_id: str) -> Dict[str, Any]:
        """Send verification code for SMS/Email MFA."""
        mfa_settings = self.db.query(MFASettings).filter(
            MFASettings.user_id == user_id,
            MFASettings.is_enabled == True,
        ).first()
        
        if not mfa_settings:
            return {"success": False, "error": "MFA not enabled"}
        
        method = MFAMethod(mfa_settings.method)
        
        if method == MFAMethod.SMS:
            phone = decrypt_field(mfa_settings.phone_number_encrypted)
            self.mfa.send_sms_code(user_id, phone)
            return {"success": True, "message": "Code sent via SMS"}
        
        elif method == MFAMethod.EMAIL:
            email = mfa_settings.verification_email
            self.mfa.send_email_code(user_id, email)
            return {"success": True, "message": "Code sent via email"}
        
        return {"success": False, "error": "Method does not require sending code"}
    
    async def disable_mfa(self, user_id: str, code: str) -> Dict[str, Any]:
        """Disable MFA (requires verification)."""
        # First verify the code
        result = await self.verify_code(user_id, code)
        
        if not result["success"]:
            return result
        
        mfa_settings = self.db.query(MFASettings).filter(
            MFASettings.user_id == user_id
        ).first()
        
        if mfa_settings:
            mfa_settings.is_enabled = False
            mfa_settings.is_verified = False
            mfa_settings.totp_secret_encrypted = None
            mfa_settings.backup_codes_hash = []
            self.db.commit()
        
        logger.info(f"MFA disabled for user {user_id}")
        
        return {"success": True, "message": "MFA disabled"}
    
    async def regenerate_backup_codes(self, user_id: str, code: str) -> Dict[str, Any]:
        """Regenerate backup codes (requires verification)."""
        # First verify the code
        result = await self.verify_code(user_id, code)
        
        if not result["success"]:
            return result
        
        mfa_settings = self.db.query(MFASettings).filter(
            MFASettings.user_id == user_id,
            MFASettings.is_enabled == True,
        ).first()
        
        if not mfa_settings:
            return {"success": False, "error": "MFA not enabled"}
        
        # Generate new backup codes
        new_codes = self.mfa._generate_backup_codes()
        mfa_settings.backup_codes_hash = self.mfa.hash_backup_codes(new_codes)
        mfa_settings.backup_codes_remaining = len(new_codes)
        self.db.commit()
        
        logger.info(f"Backup codes regenerated for user {user_id}")
        
        return {
            "success": True,
            "backup_codes": new_codes,
        }
    
    def get_mfa_status(self, user_id: str) -> Dict[str, Any]:
        """Get MFA status for a user."""
        mfa_settings = self.db.query(MFASettings).filter(
            MFASettings.user_id == user_id
        ).first()
        
        if not mfa_settings:
            return {
                "enabled": False,
                "method": None,
                "verified": False,
            }
        
        return {
            "enabled": mfa_settings.is_enabled,
            "method": mfa_settings.method,
            "verified": mfa_settings.is_verified,
            "backup_codes_remaining": mfa_settings.backup_codes_remaining,
            "last_used": mfa_settings.last_used_at.isoformat() if mfa_settings.last_used_at else None,
        }
    
    def is_mfa_required(self, user_id: str, is_admin: bool = False) -> bool:
        """Check if MFA is required for user."""
        from app.security.config import get_security_config
        
        config = get_security_config().mfa_policy
        
        if config.required:
            return True
        
        if is_admin and config.required_for_admins:
            return True
        
        return False
```

---

## File 5: Security Module Init
**Path:** `backend/app/security/__init__.py`

```python
"""
Security Module
Enterprise-grade security features for LogiAccounting Pro
"""

from app.security.config import (
    SecurityConfig,
    SecurityLevel,
    PasswordPolicy,
    SessionPolicy,
    MFAPolicy,
    RateLimitPolicy,
    EncryptionPolicy,
    AuditPolicy,
    security_config,
    get_security_config,
    configure_security,
)


__all__ = [
    # Configuration
    'SecurityConfig',
    'SecurityLevel',
    'PasswordPolicy',
    'SessionPolicy',
    'MFAPolicy',
    'RateLimitPolicy',
    'EncryptionPolicy',
    'AuditPolicy',
    'security_config',
    'get_security_config',
    'configure_security',
]


def init_security():
    """Initialize security module."""
    import logging
    
    logger = logging.getLogger("app.security")
    
    config = get_security_config()
    warnings = config.validate()
    
    for warning in warnings:
        logger.warning(f"Security warning: {warning}")
    
    logger.info(f"Security module initialized (environment: {config.environment})")
    
    return True
```

---

## Summary Part 1

| File | Description | Lines |
|------|-------------|-------|
| `security/config.py` | Security configuration | ~320 |
| `security/auth/mfa.py` | MFA core implementation | ~340 |
| `security/auth/mfa_models.py` | MFA database models | ~110 |
| `security/auth/mfa_service.py` | MFA service layer | ~280 |
| `security/__init__.py` | Security module init | ~50 |
| **Total** | | **~1,100 lines** |
