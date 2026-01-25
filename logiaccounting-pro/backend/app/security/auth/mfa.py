"""
Multi-Factor Authentication Manager
TOTP, SMS, and Email verification for LogiAccounting Pro
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MFAMethod(str, Enum):
    """Supported MFA methods."""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    HARDWARE_KEY = "hardware_key"
    BACKUP_CODE = "backup_code"


@dataclass
class MFAVerificationResult:
    """Result of MFA verification attempt."""
    success: bool
    method: MFAMethod
    message: str
    remaining_attempts: Optional[int] = None
    lockout_until: Optional[datetime] = None
    recovery_code_used: bool = False
    device_trusted: bool = False


class MFAManager:
    """
    Multi-Factor Authentication Manager.
    Handles TOTP generation/verification, SMS codes, and email verification.
    """

    def __init__(
        self,
        issuer: str = "LogiAccounting Pro",
        totp_digits: int = 6,
        totp_period: int = 30,
        totp_algorithm: str = "SHA1",
        sms_code_length: int = 6,
        email_code_length: int = 6,
        max_attempts: int = 3,
        lockout_duration_minutes: int = 15,
    ):
        self.issuer = issuer
        self.totp_digits = totp_digits
        self.totp_period = totp_period
        self.totp_algorithm = totp_algorithm
        self.sms_code_length = sms_code_length
        self.email_code_length = email_code_length
        self.max_attempts = max_attempts
        self.lockout_duration_minutes = lockout_duration_minutes

        self._pending_codes: Dict[str, Dict[str, Any]] = {}
        self._attempt_tracker: Dict[str, List[datetime]] = {}

    def generate_totp_secret(self, length: int = 32) -> str:
        """Generate a random TOTP secret."""
        random_bytes = secrets.token_bytes(length)
        return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")

    def get_totp_provisioning_uri(
        self,
        secret: str,
        account_name: str,
        issuer: Optional[str] = None,
    ) -> str:
        """Generate TOTP provisioning URI for authenticator apps."""
        issuer = issuer or self.issuer
        encoded_issuer = issuer.replace(" ", "%20")
        encoded_account = account_name.replace(" ", "%20")

        uri = (
            f"otpauth://totp/{encoded_issuer}:{encoded_account}"
            f"?secret={secret}"
            f"&issuer={encoded_issuer}"
            f"&algorithm={self.totp_algorithm}"
            f"&digits={self.totp_digits}"
            f"&period={self.totp_period}"
        )

        return uri

    def _get_hash_algorithm(self):
        """Get the hash algorithm for TOTP."""
        algorithms = {
            "SHA1": hashlib.sha1,
            "SHA256": hashlib.sha256,
            "SHA512": hashlib.sha512,
        }
        return algorithms.get(self.totp_algorithm, hashlib.sha1)

    def _generate_totp(self, secret: str, timestamp: Optional[int] = None) -> str:
        """Generate TOTP code for given timestamp."""
        if timestamp is None:
            timestamp = int(time.time())

        time_counter = timestamp // self.totp_period

        padding = "=" * ((8 - len(secret)) % 8)
        secret_bytes = base64.b32decode(secret.upper() + padding)

        counter_bytes = struct.pack(">Q", time_counter)

        hash_func = self._get_hash_algorithm()
        hmac_hash = hmac.new(secret_bytes, counter_bytes, hash_func).digest()

        offset = hmac_hash[-1] & 0x0F
        truncated = struct.unpack(">I", hmac_hash[offset:offset + 4])[0]
        truncated &= 0x7FFFFFFF

        code = truncated % (10 ** self.totp_digits)
        return str(code).zfill(self.totp_digits)

    def verify_totp(
        self,
        secret: str,
        code: str,
        window: int = 1,
    ) -> bool:
        """
        Verify TOTP code with time window tolerance.

        Args:
            secret: The TOTP secret
            code: The code to verify
            window: Number of periods before/after to check

        Returns:
            True if code is valid
        """
        if not code or len(code) != self.totp_digits:
            return False

        current_time = int(time.time())

        for offset in range(-window, window + 1):
            check_time = current_time + (offset * self.totp_period)
            expected_code = self._generate_totp(secret, check_time)

            if hmac.compare_digest(code, expected_code):
                return True

        return False

    def generate_sms_code(self, user_id: str, phone_number: str) -> Tuple[str, datetime]:
        """Generate SMS verification code."""
        code = "".join(secrets.choice("0123456789") for _ in range(self.sms_code_length))
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        self._pending_codes[f"sms:{user_id}"] = {
            "code": code,
            "phone_number": phone_number,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        }

        logger.info(f"Generated SMS code for user {user_id}")
        return code, expires_at

    def verify_sms_code(self, user_id: str, code: str) -> MFAVerificationResult:
        """Verify SMS code."""
        key = f"sms:{user_id}"

        if key not in self._pending_codes:
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.SMS,
                message="No pending SMS verification",
            )

        pending = self._pending_codes[key]

        if datetime.utcnow() > pending["expires_at"]:
            del self._pending_codes[key]
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.SMS,
                message="SMS code has expired",
            )

        if hmac.compare_digest(code, pending["code"]):
            del self._pending_codes[key]
            return MFAVerificationResult(
                success=True,
                method=MFAMethod.SMS,
                message="SMS verification successful",
            )

        return MFAVerificationResult(
            success=False,
            method=MFAMethod.SMS,
            message="Invalid SMS code",
        )

    def generate_email_code(self, user_id: str, email: str) -> Tuple[str, datetime]:
        """Generate email verification code."""
        code = "".join(secrets.choice("0123456789") for _ in range(self.email_code_length))
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        self._pending_codes[f"email:{user_id}"] = {
            "code": code,
            "email": email,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        }

        logger.info(f"Generated email code for user {user_id}")
        return code, expires_at

    def verify_email_code(self, user_id: str, code: str) -> MFAVerificationResult:
        """Verify email code."""
        key = f"email:{user_id}"

        if key not in self._pending_codes:
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.EMAIL,
                message="No pending email verification",
            )

        pending = self._pending_codes[key]

        if datetime.utcnow() > pending["expires_at"]:
            del self._pending_codes[key]
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.EMAIL,
                message="Email code has expired",
            )

        if hmac.compare_digest(code, pending["code"]):
            del self._pending_codes[key]
            return MFAVerificationResult(
                success=True,
                method=MFAMethod.EMAIL,
                message="Email verification successful",
            )

        return MFAVerificationResult(
            success=False,
            method=MFAMethod.EMAIL,
            message="Invalid email code",
        )

    def generate_recovery_codes(self, count: int = 10, length: int = 8) -> List[str]:
        """Generate backup recovery codes."""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(length // 2).upper()
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes

    def hash_recovery_code(self, code: str) -> str:
        """Hash a recovery code for storage."""
        normalized = code.replace("-", "").upper()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def verify_recovery_code(self, code: str, hashed_codes: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Verify a recovery code against stored hashes.

        Returns:
            Tuple of (success, used_hash) where used_hash should be removed from storage
        """
        code_hash = self.hash_recovery_code(code)

        for stored_hash in hashed_codes:
            if hmac.compare_digest(code_hash, stored_hash):
                return True, stored_hash

        return False, None

    def check_rate_limit(self, user_id: str) -> Tuple[bool, Optional[int], Optional[datetime]]:
        """
        Check if user is rate limited.

        Returns:
            Tuple of (allowed, remaining_attempts, lockout_until)
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.lockout_duration_minutes)

        if user_id not in self._attempt_tracker:
            self._attempt_tracker[user_id] = []

        self._attempt_tracker[user_id] = [
            attempt for attempt in self._attempt_tracker[user_id]
            if attempt > cutoff
        ]

        attempts = len(self._attempt_tracker[user_id])

        if attempts >= self.max_attempts:
            oldest_attempt = min(self._attempt_tracker[user_id])
            lockout_until = oldest_attempt + timedelta(minutes=self.lockout_duration_minutes)
            return False, 0, lockout_until

        remaining = self.max_attempts - attempts
        return True, remaining, None

    def record_attempt(self, user_id: str, success: bool) -> None:
        """Record a verification attempt."""
        if user_id not in self._attempt_tracker:
            self._attempt_tracker[user_id] = []

        if not success:
            self._attempt_tracker[user_id].append(datetime.utcnow())
        else:
            self._attempt_tracker[user_id] = []

    def generate_device_token(self, user_id: str, device_id: str) -> str:
        """Generate a trusted device token."""
        data = f"{user_id}:{device_id}:{secrets.token_hex(16)}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_complete(
        self,
        user_id: str,
        method: MFAMethod,
        code: str,
        secret: Optional[str] = None,
        recovery_codes: Optional[List[str]] = None,
    ) -> MFAVerificationResult:
        """
        Complete MFA verification workflow.

        Args:
            user_id: The user ID
            method: The MFA method being used
            code: The verification code
            secret: TOTP secret (required for TOTP method)
            recovery_codes: List of hashed recovery codes (for backup code method)

        Returns:
            MFAVerificationResult with verification status
        """
        allowed, remaining, lockout_until = self.check_rate_limit(user_id)

        if not allowed:
            return MFAVerificationResult(
                success=False,
                method=method,
                message="Too many failed attempts. Please try again later.",
                remaining_attempts=0,
                lockout_until=lockout_until,
            )

        result = None

        if method == MFAMethod.TOTP:
            if not secret:
                result = MFAVerificationResult(
                    success=False,
                    method=method,
                    message="TOTP secret not configured",
                )
            else:
                success = self.verify_totp(secret, code)
                result = MFAVerificationResult(
                    success=success,
                    method=method,
                    message="Verification successful" if success else "Invalid code",
                )

        elif method == MFAMethod.SMS:
            result = self.verify_sms_code(user_id, code)

        elif method == MFAMethod.EMAIL:
            result = self.verify_email_code(user_id, code)

        elif method == MFAMethod.BACKUP_CODE:
            if not recovery_codes:
                result = MFAVerificationResult(
                    success=False,
                    method=method,
                    message="No recovery codes available",
                )
            else:
                success, _ = self.verify_recovery_code(code, recovery_codes)
                result = MFAVerificationResult(
                    success=success,
                    method=method,
                    message="Recovery code accepted" if success else "Invalid recovery code",
                    recovery_code_used=success,
                )

        else:
            result = MFAVerificationResult(
                success=False,
                method=method,
                message=f"Unsupported MFA method: {method}",
            )

        self.record_attempt(user_id, result.success)

        if not result.success:
            result.remaining_attempts = remaining - 1 if remaining else 0

        return result
