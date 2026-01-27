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
