"""
Token Manager
JWT token generation and validation for LogiAccounting Pro
"""

import secrets
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Set
import logging

from app.utils.datetime_utils import utc_now
import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError,
    InvalidSignatureError,
    DecodeError,
)

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Types of tokens."""
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    API_KEY = "api_key"
    MFA_CHALLENGE = "mfa_challenge"
    INVITATION = "invitation"


@dataclass
class TokenPayload:
    """Decoded token payload."""
    token_type: TokenType
    subject: str
    issued_at: datetime
    expires_at: datetime
    issuer: Optional[str] = None
    audience: Optional[str] = None
    jti: Optional[str] = None
    session_id: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    claims: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return utc_now() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """Check if token has a specific scope."""
        return scope in self.scopes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "token_type": self.token_type.value,
            "subject": self.subject,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "issuer": self.issuer,
            "audience": self.audience,
            "jti": self.jti,
            "session_id": self.session_id,
            "scopes": self.scopes,
            "claims": self.claims,
        }


class TokenError(Exception):
    """Base exception for token errors."""
    pass


class TokenExpiredError(TokenError):
    """Token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Token is invalid."""
    pass


class TokenRevokedError(TokenError):
    """Token has been revoked."""
    pass


class TokenManager:
    """
    JWT Token Manager.
    Handles generation, validation, and revocation of tokens.
    """

    ALGORITHM = "HS256"

    DEFAULT_EXPIRY = {
        TokenType.ACCESS: timedelta(minutes=15),
        TokenType.REFRESH: timedelta(days=7),
        TokenType.PASSWORD_RESET: timedelta(hours=1),
        TokenType.EMAIL_VERIFICATION: timedelta(hours=24),
        TokenType.API_KEY: timedelta(days=365),
        TokenType.MFA_CHALLENGE: timedelta(minutes=5),
        TokenType.INVITATION: timedelta(days=7),
    }

    def __init__(
        self,
        secret_key: str,
        issuer: str = "logiaccounting-pro",
        audience: Optional[str] = None,
        access_token_expiry: Optional[timedelta] = None,
        refresh_token_expiry: Optional[timedelta] = None,
        redis_client: Optional[Any] = None,
    ):
        self.secret_key = secret_key
        self.issuer = issuer
        self.audience = audience
        self.redis = redis_client

        self._expiry = dict(self.DEFAULT_EXPIRY)
        if access_token_expiry:
            self._expiry[TokenType.ACCESS] = access_token_expiry
        if refresh_token_expiry:
            self._expiry[TokenType.REFRESH] = refresh_token_expiry

        self._revoked_tokens: Set[str] = set()

    def _generate_jti(self) -> str:
        """Generate a unique token identifier."""
        return secrets.token_urlsafe(24)

    def create_token(
        self,
        token_type: TokenType,
        subject: str,
        scopes: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        claims: Optional[Dict[str, Any]] = None,
        expiry: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT token.

        Args:
            token_type: Type of token to create
            subject: Token subject (usually user ID)
            scopes: List of permission scopes
            session_id: Associated session ID
            claims: Additional claims to include
            expiry: Custom expiry duration

        Returns:
            Encoded JWT token string
        """
        now = utc_now()
        exp = expiry or self._expiry.get(token_type, timedelta(hours=1))
        expires_at = now + exp

        jti = self._generate_jti()

        payload = {
            "type": token_type.value,
            "sub": subject,
            "iat": now,
            "exp": expires_at,
            "iss": self.issuer,
            "jti": jti,
        }

        if self.audience:
            payload["aud"] = self.audience

        if scopes:
            payload["scopes"] = scopes

        if session_id:
            payload["sid"] = session_id

        if claims:
            payload.update(claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)

        logger.debug(
            f"Created {token_type.value} token for subject {subject}, "
            f"expires at {expires_at.isoformat()}"
        )

        return token

    def decode_token(
        self,
        token: str,
        expected_type: Optional[TokenType] = None,
        verify_exp: bool = True,
        check_revoked: bool = True,
    ) -> TokenPayload:
        """
        Decode and validate a JWT token.

        Args:
            token: The JWT token string
            expected_type: Expected token type (optional)
            verify_exp: Whether to verify expiration
            check_revoked: Whether to check revocation status

        Returns:
            TokenPayload with decoded data

        Raises:
            TokenExpiredError: If token is expired
            TokenInvalidError: If token is invalid
            TokenRevokedError: If token is revoked
        """
        try:
            options = {"verify_exp": verify_exp}

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM],
                options=options,
                issuer=self.issuer,
                audience=self.audience if self.audience else None,
            )

        except ExpiredSignatureError:
            logger.debug("Token expired")
            raise TokenExpiredError("Token has expired")

        except InvalidSignatureError:
            logger.warning("Invalid token signature")
            raise TokenInvalidError("Invalid token signature")

        except DecodeError as e:
            logger.warning(f"Token decode error: {e}")
            raise TokenInvalidError("Invalid token format")

        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise TokenInvalidError(str(e))

        token_type = TokenType(payload.get("type", TokenType.ACCESS.value))

        if expected_type and token_type != expected_type:
            raise TokenInvalidError(
                f"Expected {expected_type.value} token, got {token_type.value}"
            )

        jti = payload.get("jti")
        if check_revoked and jti and self._is_revoked(jti):
            logger.warning(f"Attempted use of revoked token: {jti[:8]}...")
            raise TokenRevokedError("Token has been revoked")

        return TokenPayload(
            token_type=token_type,
            subject=payload.get("sub", ""),
            issued_at=datetime.fromtimestamp(payload.get("iat", 0)),
            expires_at=datetime.fromtimestamp(payload.get("exp", 0)),
            issuer=payload.get("iss"),
            audience=payload.get("aud"),
            jti=jti,
            session_id=payload.get("sid"),
            scopes=payload.get("scopes", []),
            claims={
                k: v for k, v in payload.items()
                if k not in ["type", "sub", "iat", "exp", "iss", "aud", "jti", "sid", "scopes"]
            },
        )

    def create_access_token(
        self,
        user_id: str,
        scopes: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create an access token."""
        return self.create_token(
            token_type=TokenType.ACCESS,
            subject=user_id,
            scopes=scopes,
            session_id=session_id,
            claims=claims,
        )

    def create_refresh_token(
        self,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> str:
        """Create a refresh token."""
        return self.create_token(
            token_type=TokenType.REFRESH,
            subject=user_id,
            session_id=session_id,
        )

    def create_token_pair(
        self,
        user_id: str,
        scopes: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Create an access/refresh token pair.

        Returns:
            Dict with 'access_token' and 'refresh_token'
        """
        access_token = self.create_access_token(
            user_id=user_id,
            scopes=scopes,
            session_id=session_id,
            claims=claims,
        )

        refresh_token = self.create_refresh_token(
            user_id=user_id,
            session_id=session_id,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": int(self._expiry[TokenType.ACCESS].total_seconds()),
        }

    def refresh_access_token(
        self,
        refresh_token: str,
        scopes: Optional[List[str]] = None,
        claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token
            scopes: Scopes for the new access token
            claims: Additional claims for the new access token

        Returns:
            Dict with new 'access_token'
        """
        payload = self.decode_token(refresh_token, expected_type=TokenType.REFRESH)

        access_token = self.create_access_token(
            user_id=payload.subject,
            scopes=scopes,
            session_id=payload.session_id,
            claims=claims,
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": int(self._expiry[TokenType.ACCESS].total_seconds()),
        }

    def create_password_reset_token(self, user_id: str, email: str) -> str:
        """Create a password reset token."""
        return self.create_token(
            token_type=TokenType.PASSWORD_RESET,
            subject=user_id,
            claims={"email": email},
        )

    def create_email_verification_token(self, user_id: str, email: str) -> str:
        """Create an email verification token."""
        return self.create_token(
            token_type=TokenType.EMAIL_VERIFICATION,
            subject=user_id,
            claims={"email": email},
        )

    def create_mfa_challenge_token(
        self,
        user_id: str,
        challenge_id: str,
        method: str,
    ) -> str:
        """Create an MFA challenge token."""
        return self.create_token(
            token_type=TokenType.MFA_CHALLENGE,
            subject=user_id,
            claims={
                "challenge_id": challenge_id,
                "method": method,
            },
        )

    def create_invitation_token(
        self,
        inviter_id: str,
        email: str,
        role: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> str:
        """Create an invitation token."""
        claims = {"email": email}
        if role:
            claims["role"] = role
        if organization_id:
            claims["organization_id"] = organization_id

        return self.create_token(
            token_type=TokenType.INVITATION,
            subject=inviter_id,
            claims=claims,
        )

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: Optional[List[str]] = None,
        expiry_days: int = 365,
    ) -> tuple[str, str]:
        """
        Create an API key.

        Returns:
            Tuple of (api_key, key_id) where key_id can be used for revocation
        """
        key_id = self._generate_jti()

        token = self.create_token(
            token_type=TokenType.API_KEY,
            subject=user_id,
            scopes=scopes,
            claims={"name": name, "key_id": key_id},
            expiry=timedelta(days=expiry_days),
        )

        logger.info(f"Created API key '{name}' for user {user_id}")

        return token, key_id

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a token.

        Args:
            token: The token to revoke

        Returns:
            True if revoked successfully
        """
        try:
            payload = self.decode_token(token, verify_exp=False, check_revoked=False)
        except TokenInvalidError:
            return False

        if not payload.jti:
            return False

        await self._add_to_revocation_list(payload.jti, payload.expires_at)

        logger.info(f"Revoked token: {payload.jti[:8]}...")

        return True

    async def revoke_all_user_tokens(self, user_id: str) -> bool:
        """
        Revoke all tokens for a user.
        Note: This requires tracking user tokens separately.
        """
        if self.redis:
            user_key = f"user_tokens:{user_id}"
            token_jtis = await self.redis.smembers(user_key)

            for jti in token_jtis:
                jti_str = jti.decode() if isinstance(jti, bytes) else jti
                await self._add_to_revocation_list(
                    jti_str,
                    utc_now() + timedelta(days=7),
                )

            await self.redis.delete(user_key)

            logger.info(f"Revoked all tokens for user {user_id}")
            return True

        return False

    async def _add_to_revocation_list(self, jti: str, expires_at: datetime) -> None:
        """Add a token JTI to the revocation list."""
        if self.redis:
            key = f"revoked_token:{jti}"
            ttl = int((expires_at - utc_now()).total_seconds())
            if ttl > 0:
                await self.redis.setex(key, ttl, "1")
        else:
            self._revoked_tokens.add(jti)

    def _is_revoked(self, jti: str) -> bool:
        """Check if a token is revoked."""
        if self.redis:
            import asyncio

            async def check():
                key = f"revoked_token:{jti}"
                return await self.redis.exists(key)

            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(check())
            except RuntimeError:
                return False
        else:
            return jti in self._revoked_tokens

    def verify_token_signature(self, token: str) -> bool:
        """
        Verify only the token signature (not expiration).
        Useful for logging out with expired tokens.
        """
        try:
            self.decode_token(token, verify_exp=False, check_revoked=False)
            return True
        except TokenInvalidError:
            return False

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token information without full validation.
        Decodes the token without verifying signature.
        """
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
            )

            return {
                "type": payload.get("type"),
                "subject": payload.get("sub"),
                "issued_at": datetime.fromtimestamp(payload.get("iat", 0)).isoformat(),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)).isoformat(),
                "is_expired": datetime.fromtimestamp(payload.get("exp", 0)) < utc_now(),
                "jti": payload.get("jti"),
            }
        except Exception:
            return None

    def hash_token(self, token: str) -> str:
        """Create a hash of a token for storage/logging."""
        return hashlib.sha256(token.encode()).hexdigest()

    def cleanup_expired_revocations(self) -> int:
        """
        Clean up expired entries from in-memory revocation list.
        Only applicable for non-Redis mode.

        Returns:
            Number of entries removed
        """
        if self.redis:
            return 0

        initial_count = len(self._revoked_tokens)
        self._revoked_tokens.clear()

        logger.info(f"Cleared {initial_count} entries from revocation list")

        return initial_count
