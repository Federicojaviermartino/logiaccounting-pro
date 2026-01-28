"""
MFA Database Models
SQLAlchemy models for Multi-Factor Authentication
"""

from datetime import datetime
from typing import Optional, List

from app.utils.datetime_utils import utc_now
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from app.models.base import Base, TimestampMixin


class MFAMethodType(str, enum.Enum):
    """MFA method types."""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    HARDWARE_KEY = "hardware_key"


class MFAChallengeStatus(str, enum.Enum):
    """MFA challenge status."""
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


class MFASettings(Base, TimestampMixin):
    """User MFA settings and configuration."""

    __tablename__ = "mfa_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    enabled = Column(Boolean, default=False, nullable=False)
    primary_method = Column(SQLEnum(MFAMethodType), default=MFAMethodType.TOTP)

    totp_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(64), nullable=True)
    totp_verified = Column(Boolean, default=False)
    totp_verified_at = Column(DateTime, nullable=True)

    sms_enabled = Column(Boolean, default=False)
    sms_phone_number = Column(String(20), nullable=True)
    sms_verified = Column(Boolean, default=False)
    sms_verified_at = Column(DateTime, nullable=True)

    email_enabled = Column(Boolean, default=False)
    email_address = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)

    hardware_key_enabled = Column(Boolean, default=False)
    hardware_key_data = Column(JSONB, nullable=True)
    hardware_key_verified_at = Column(DateTime, nullable=True)

    recovery_codes_generated = Column(Boolean, default=False)
    recovery_codes_generated_at = Column(DateTime, nullable=True)
    recovery_codes_remaining = Column(Integer, default=0)

    remember_device_enabled = Column(Boolean, default=True)
    remember_device_days = Column(Integer, default=30)

    last_used_at = Column(DateTime, nullable=True)
    last_used_method = Column(SQLEnum(MFAMethodType), nullable=True)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

    metadata_json = Column(JSONB, default=dict)

    recovery_codes = relationship(
        "MFARecoveryCode",
        back_populates="mfa_settings",
        cascade="all, delete-orphan",
    )
    challenges = relationship(
        "MFAChallenge",
        back_populates="mfa_settings",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_mfa_settings_user_id", "user_id"),
        Index("ix_mfa_settings_enabled", "enabled"),
    )

    def is_locked(self) -> bool:
        """Check if MFA is currently locked due to failed attempts."""
        if self.locked_until is None:
            return False
        return utc_now() < self.locked_until

    def increment_failed_attempts(self, max_attempts: int = 5, lockout_minutes: int = 15) -> None:
        """Increment failed attempts and lock if threshold reached."""
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = utc_now() + timedelta(minutes=lockout_minutes)

    def reset_failed_attempts(self) -> None:
        """Reset failed attempts counter."""
        self.failed_attempts = 0
        self.locked_until = None

    def record_successful_verification(self, method: MFAMethodType) -> None:
        """Record a successful MFA verification."""
        self.last_used_at = utc_now()
        self.last_used_method = method
        self.reset_failed_attempts()

    def get_enabled_methods(self) -> List[MFAMethodType]:
        """Get list of enabled MFA methods."""
        methods = []
        if self.totp_enabled and self.totp_verified:
            methods.append(MFAMethodType.TOTP)
        if self.sms_enabled and self.sms_verified:
            methods.append(MFAMethodType.SMS)
        if self.email_enabled and self.email_verified:
            methods.append(MFAMethodType.EMAIL)
        if self.hardware_key_enabled:
            methods.append(MFAMethodType.HARDWARE_KEY)
        return methods

    def to_dict(self) -> dict:
        """Convert to dictionary (excluding secrets)."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "enabled": self.enabled,
            "primary_method": self.primary_method.value if self.primary_method else None,
            "totp_enabled": self.totp_enabled,
            "totp_verified": self.totp_verified,
            "sms_enabled": self.sms_enabled,
            "sms_verified": self.sms_verified,
            "sms_phone_number": self.sms_phone_number[-4:] if self.sms_phone_number else None,
            "email_enabled": self.email_enabled,
            "email_verified": self.email_verified,
            "hardware_key_enabled": self.hardware_key_enabled,
            "recovery_codes_remaining": self.recovery_codes_remaining,
            "remember_device_enabled": self.remember_device_enabled,
            "enabled_methods": [m.value for m in self.get_enabled_methods()],
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


class MFARecoveryCode(Base, TimestampMixin):
    """MFA recovery/backup codes."""

    __tablename__ = "mfa_recovery_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mfa_settings_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mfa_settings.id", ondelete="CASCADE"),
        nullable=False,
    )

    code_hash = Column(String(64), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    used_ip = Column(String(45), nullable=True)
    used_user_agent = Column(String(512), nullable=True)

    mfa_settings = relationship("MFASettings", back_populates="recovery_codes")

    __table_args__ = (
        Index("ix_mfa_recovery_codes_settings_id", "mfa_settings_id"),
        Index("ix_mfa_recovery_codes_code_hash", "code_hash"),
        Index("ix_mfa_recovery_codes_used", "used"),
    )

    def mark_used(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        """Mark this recovery code as used."""
        self.used = True
        self.used_at = utc_now()
        self.used_ip = ip_address
        self.used_user_agent = user_agent[:512] if user_agent else None


class MFAChallenge(Base, TimestampMixin):
    """MFA challenge/verification attempts."""

    __tablename__ = "mfa_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mfa_settings_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mfa_settings.id", ondelete="CASCADE"),
        nullable=False,
    )

    method = Column(SQLEnum(MFAMethodType), nullable=False)
    status = Column(SQLEnum(MFAChallengeStatus), default=MFAChallengeStatus.PENDING)

    code_hash = Column(String(64), nullable=True)
    challenge_data = Column(JSONB, nullable=True)

    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    device_id = Column(String(64), nullable=True)

    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    session_id = Column(String(64), nullable=True)
    purpose = Column(String(50), default="login")

    mfa_settings = relationship("MFASettings", back_populates="challenges")

    __table_args__ = (
        Index("ix_mfa_challenges_settings_id", "mfa_settings_id"),
        Index("ix_mfa_challenges_status", "status"),
        Index("ix_mfa_challenges_expires_at", "expires_at"),
        Index("ix_mfa_challenges_session_id", "session_id"),
    )

    def is_expired(self) -> bool:
        """Check if this challenge has expired."""
        return utc_now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if this challenge can still be verified."""
        return (
            self.status == MFAChallengeStatus.PENDING
            and not self.is_expired()
            and self.attempts < self.max_attempts
        )

    def record_attempt(self, success: bool) -> None:
        """Record a verification attempt."""
        self.attempts += 1

        if success:
            self.status = MFAChallengeStatus.VERIFIED
            self.verified_at = utc_now()
        elif self.attempts >= self.max_attempts:
            self.status = MFAChallengeStatus.FAILED

    def mark_expired(self) -> None:
        """Mark this challenge as expired."""
        self.status = MFAChallengeStatus.EXPIRED

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "method": self.method.value,
            "status": self.status.value,
            "expires_at": self.expires_at.isoformat(),
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "purpose": self.purpose,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TrustedDevice(Base, TimestampMixin):
    """Trusted devices that skip MFA."""

    __tablename__ = "trusted_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    device_token_hash = Column(String(64), nullable=False, unique=True)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)

    browser = Column(String(100), nullable=True)
    browser_version = Column(String(50), nullable=True)
    os_name = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)

    ip_address = Column(String(45), nullable=True)
    location = Column(String(255), nullable=True)

    trusted_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_trusted_devices_user_id", "user_id"),
        Index("ix_trusted_devices_token_hash", "device_token_hash"),
        Index("ix_trusted_devices_expires_at", "expires_at"),
        Index("ix_trusted_devices_active", "is_active"),
    )

    def is_valid(self) -> bool:
        """Check if this trusted device is still valid."""
        return (
            self.is_active
            and self.revoked_at is None
            and utc_now() < self.expires_at
        )

    def revoke(self, reason: Optional[str] = None) -> None:
        """Revoke this trusted device."""
        self.is_active = False
        self.revoked_at = utc_now()
        self.revoked_reason = reason

    def record_use(self) -> None:
        """Record that this device was used."""
        self.last_used_at = utc_now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "device_name": self.device_name,
            "device_type": self.device_type,
            "browser": self.browser,
            "os_name": self.os_name,
            "location": self.location,
            "trusted_at": self.trusted_at.isoformat() if self.trusted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active,
        }
