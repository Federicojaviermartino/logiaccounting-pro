"""
Security Configuration
Centralized security settings for LogiAccounting Pro
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import os


class SecurityLevel(str, Enum):
    """Security level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PasswordPolicy:
    """Password policy configuration."""
    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special: bool = True
    special_characters: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    min_uppercase: int = 1
    min_lowercase: int = 1
    min_digits: int = 1
    min_special: int = 1
    max_consecutive_chars: int = 3
    password_history: int = 12
    max_age_days: int = 90
    min_age_days: int = 1
    lockout_threshold: int = 5
    lockout_duration_minutes: int = 30
    require_change_on_first_login: bool = True
    prevent_username_in_password: bool = True
    prevent_email_in_password: bool = True
    dictionary_check: bool = True
    common_passwords_check: bool = True

    def validate_password(self, password: str, username: str = None, email: str = None) -> List[str]:
        """Validate password against policy."""
        errors = []

        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")

        if len(password) > self.max_length:
            errors.append(f"Password must not exceed {self.max_length} characters")

        if self.require_uppercase and sum(1 for c in password if c.isupper()) < self.min_uppercase:
            errors.append(f"Password must contain at least {self.min_uppercase} uppercase letter(s)")

        if self.require_lowercase and sum(1 for c in password if c.islower()) < self.min_lowercase:
            errors.append(f"Password must contain at least {self.min_lowercase} lowercase letter(s)")

        if self.require_digits and sum(1 for c in password if c.isdigit()) < self.min_digits:
            errors.append(f"Password must contain at least {self.min_digits} digit(s)")

        if self.require_special:
            special_count = sum(1 for c in password if c in self.special_characters)
            if special_count < self.min_special:
                errors.append(f"Password must contain at least {self.min_special} special character(s)")

        if self.max_consecutive_chars > 0:
            for i in range(len(password) - self.max_consecutive_chars):
                if len(set(password[i:i + self.max_consecutive_chars + 1])) == 1:
                    errors.append(f"Password cannot have more than {self.max_consecutive_chars} consecutive identical characters")
                    break

        if self.prevent_username_in_password and username:
            if username.lower() in password.lower():
                errors.append("Password cannot contain username")

        if self.prevent_email_in_password and email:
            email_local = email.split("@")[0].lower()
            if email_local in password.lower():
                errors.append("Password cannot contain email address")

        return errors


@dataclass
class SessionPolicy:
    """Session management policy."""
    session_timeout_minutes: int = 30
    absolute_timeout_hours: int = 24
    max_concurrent_sessions: int = 5
    session_extension_enabled: bool = True
    session_extension_minutes: int = 15
    require_reauth_for_sensitive: bool = True
    reauth_timeout_minutes: int = 5
    bind_to_ip: bool = False
    bind_to_user_agent: bool = True
    rotate_session_on_auth: bool = True
    secure_cookie: bool = True
    http_only_cookie: bool = True
    same_site_cookie: str = "strict"
    cookie_domain: Optional[str] = None
    cookie_path: str = "/"

    def get_cookie_settings(self) -> Dict[str, Any]:
        """Get cookie configuration settings."""
        return {
            "secure": self.secure_cookie,
            "httponly": self.http_only_cookie,
            "samesite": self.same_site_cookie,
            "domain": self.cookie_domain,
            "path": self.cookie_path,
        }


@dataclass
class MFAPolicy:
    """Multi-factor authentication policy."""
    enabled: bool = True
    required_for_admins: bool = True
    required_for_all: bool = False
    allowed_methods: List[str] = field(default_factory=lambda: ["totp", "sms", "email"])
    default_method: str = "totp"
    totp_issuer: str = "LogiAccounting Pro"
    totp_digits: int = 6
    totp_period: int = 30
    totp_algorithm: str = "SHA1"
    sms_code_length: int = 6
    sms_code_expiry_minutes: int = 5
    email_code_length: int = 6
    email_code_expiry_minutes: int = 10
    max_verification_attempts: int = 3
    lockout_duration_minutes: int = 15
    recovery_codes_count: int = 10
    recovery_code_length: int = 8
    remember_device_days: int = 30
    require_mfa_for_password_change: bool = True
    require_mfa_for_sensitive_actions: bool = True


@dataclass
class RateLimitPolicy:
    """Rate limiting policy."""
    enabled: bool = True
    default_requests_per_minute: int = 60
    default_requests_per_hour: int = 1000
    login_attempts_per_minute: int = 5
    login_attempts_per_hour: int = 20
    api_requests_per_minute: int = 100
    api_requests_per_hour: int = 5000
    password_reset_per_hour: int = 3
    mfa_verification_per_minute: int = 5
    file_upload_per_hour: int = 50
    report_generation_per_hour: int = 20
    burst_multiplier: float = 1.5
    whitelist_ips: List[str] = field(default_factory=list)
    blacklist_ips: List[str] = field(default_factory=list)
    by_user: bool = True
    by_ip: bool = True
    by_endpoint: bool = True
    redis_backend: bool = True
    sliding_window: bool = True


@dataclass
class EncryptionPolicy:
    """Encryption policy configuration."""
    algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2"
    key_derivation_iterations: int = 100000
    salt_length: int = 32
    nonce_length: int = 12
    tag_length: int = 16
    encrypt_pii: bool = True
    encrypt_financial_data: bool = True
    encrypt_at_rest: bool = True
    encrypt_in_transit: bool = True
    key_rotation_days: int = 90
    master_key_source: str = "environment"
    field_level_encryption: bool = True
    searchable_encryption: bool = False
    backup_encryption: bool = True
    log_encryption: bool = False

    pii_fields: List[str] = field(default_factory=lambda: [
        "ssn", "social_security_number", "tax_id", "ein",
        "bank_account", "routing_number", "credit_card",
        "passport_number", "drivers_license"
    ])

    financial_fields: List[str] = field(default_factory=lambda: [
        "salary", "bank_balance", "investment_amount",
        "loan_amount", "payment_amount"
    ])


@dataclass
class AuditPolicy:
    """Audit logging policy."""
    enabled: bool = True
    log_authentication: bool = True
    log_authorization: bool = True
    log_data_access: bool = True
    log_data_modification: bool = True
    log_admin_actions: bool = True
    log_security_events: bool = True
    log_api_calls: bool = True
    log_failed_attempts: bool = True
    log_user_actions: bool = True
    include_request_body: bool = False
    include_response_body: bool = False
    mask_sensitive_data: bool = True
    retention_days: int = 2555
    archive_enabled: bool = True
    archive_after_days: int = 90
    archive_storage: str = "s3"
    integrity_check: bool = True
    tamper_detection: bool = True
    real_time_alerts: bool = True
    alert_on_suspicious: bool = True
    compliance_mode: str = "sox"

    sensitive_fields: List[str] = field(default_factory=lambda: [
        "password", "token", "secret", "key", "credential",
        "ssn", "credit_card", "bank_account", "api_key"
    ])


@dataclass
class SecurityConfig:
    """Main security configuration."""
    environment: str = "production"
    security_level: SecurityLevel = SecurityLevel.HIGH
    debug_mode: bool = False
    password_policy: PasswordPolicy = field(default_factory=PasswordPolicy)
    session_policy: SessionPolicy = field(default_factory=SessionPolicy)
    mfa_policy: MFAPolicy = field(default_factory=MFAPolicy)
    rate_limit_policy: RateLimitPolicy = field(default_factory=RateLimitPolicy)
    encryption_policy: EncryptionPolicy = field(default_factory=EncryptionPolicy)
    audit_policy: AuditPolicy = field(default_factory=AuditPolicy)

    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["https://app.logiaccounting.com"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH"])
    cors_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization", "X-Request-ID"])
    cors_credentials: bool = True
    cors_max_age: int = 600

    csp_enabled: bool = True
    csp_directives: Dict[str, str] = field(default_factory=lambda: {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self' 'unsafe-inline'",
        "img-src": "'self' data: https:",
        "font-src": "'self'",
        "connect-src": "'self'",
        "frame-ancestors": "'none'",
        "form-action": "'self'",
        "base-uri": "'self'",
    })

    hsts_enabled: bool = True
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True

    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"

    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    geo_blocking_enabled: bool = False
    blocked_countries: List[str] = field(default_factory=list)
    allowed_countries: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """Validate security configuration."""
        warnings = []

        if self.debug_mode and self.environment == "production":
            warnings.append("Debug mode is enabled in production environment")

        if self.security_level == SecurityLevel.LOW:
            warnings.append("Security level is set to LOW")

        if not self.mfa_policy.enabled:
            warnings.append("MFA is disabled")

        if not self.rate_limit_policy.enabled:
            warnings.append("Rate limiting is disabled")

        if not self.audit_policy.enabled:
            warnings.append("Audit logging is disabled")

        if self.password_policy.min_length < 8:
            warnings.append("Password minimum length is below recommended 8 characters")

        if not self.hsts_enabled:
            warnings.append("HSTS is disabled")

        if not self.csp_enabled:
            warnings.append("Content Security Policy is disabled")

        if "*" in self.cors_origins:
            warnings.append("CORS allows all origins")

        if self.session_policy.session_timeout_minutes > 60:
            warnings.append("Session timeout exceeds 60 minutes")

        if not self.encryption_policy.encrypt_at_rest:
            warnings.append("Data encryption at rest is disabled")

        return warnings

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers based on configuration."""
        headers = {
            "X-Frame-Options": self.x_frame_options,
            "X-Content-Type-Options": self.x_content_type_options,
            "X-XSS-Protection": self.x_xss_protection,
            "Referrer-Policy": self.referrer_policy,
            "Permissions-Policy": self.permissions_policy,
        }

        if self.hsts_enabled:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value

        if self.csp_enabled:
            csp_parts = [f"{key} {value}" for key, value in self.csp_directives.items()]
            headers["Content-Security-Policy"] = "; ".join(csp_parts)

        return headers

    @classmethod
    def from_environment(cls) -> "SecurityConfig":
        """Create configuration from environment variables."""
        env = os.getenv("ENVIRONMENT", "production")
        security_level = SecurityLevel(os.getenv("SECURITY_LEVEL", "high").lower())

        config = cls(
            environment=env,
            security_level=security_level,
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
        )

        if env == "development":
            config.cors_origins = ["http://localhost:3000", "http://localhost:8000"]
            config.session_policy.secure_cookie = False
            config.hsts_enabled = False

        return config


security_config: Optional[SecurityConfig] = None


def get_security_config() -> SecurityConfig:
    """Get the current security configuration."""
    global security_config
    if security_config is None:
        security_config = SecurityConfig.from_environment()
    return security_config


def configure_security(config: SecurityConfig) -> None:
    """Set the security configuration."""
    global security_config
    security_config = config
