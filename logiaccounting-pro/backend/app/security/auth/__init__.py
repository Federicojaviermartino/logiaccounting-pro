"""
Security Authentication Module
Advanced authentication features for LogiAccounting Pro
"""

from app.security.auth.mfa import (
    MFAManager,
    MFAMethod,
    MFAVerificationResult,
)
from app.security.auth.mfa_models import (
    MFASettings,
    MFARecoveryCode,
    MFAChallenge,
)
from app.security.auth.mfa_service import (
    MFAService,
    get_mfa_service,
)
from app.security.auth.oauth import (
    OAuthManager,
    OAuthProvider,
    OAuthTokenData,
    OAuthUserInfo,
)
from app.security.auth.sessions import (
    SessionManager,
    SessionData,
    DeviceInfo,
)
from app.security.auth.tokens import (
    TokenManager,
    TokenType,
    TokenPayload,
)


__all__ = [
    # MFA
    'MFAManager',
    'MFAMethod',
    'MFAVerificationResult',
    'MFASettings',
    'MFARecoveryCode',
    'MFAChallenge',
    'MFAService',
    'get_mfa_service',
    # OAuth
    'OAuthManager',
    'OAuthProvider',
    'OAuthTokenData',
    'OAuthUserInfo',
    # Sessions
    'SessionManager',
    'SessionData',
    'DeviceInfo',
    # Tokens
    'TokenManager',
    'TokenType',
    'TokenPayload',
]
