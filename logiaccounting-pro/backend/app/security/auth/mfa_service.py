"""
MFA Service
High-level MFA operations for LogiAccounting Pro
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
import logging

from app.utils.datetime_utils import utc_now
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.security.auth.mfa import MFAManager, MFAMethod, MFAVerificationResult
from app.security.auth.mfa_models import (
    MFASettings,
    MFARecoveryCode,
    MFAChallenge,
    TrustedDevice,
    MFAMethodType,
    MFAChallengeStatus,
)
from app.security.config import get_security_config

logger = logging.getLogger(__name__)


class MFAService:
    """
    High-level MFA service for managing user MFA settings and verification.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config = get_security_config()
        self.mfa_policy = self.config.mfa_policy

        self.manager = MFAManager(
            issuer=self.mfa_policy.totp_issuer,
            totp_digits=self.mfa_policy.totp_digits,
            totp_period=self.mfa_policy.totp_period,
            totp_algorithm=self.mfa_policy.totp_algorithm,
            sms_code_length=self.mfa_policy.sms_code_length,
            email_code_length=self.mfa_policy.email_code_length,
            max_attempts=self.mfa_policy.max_verification_attempts,
            lockout_duration_minutes=self.mfa_policy.lockout_duration_minutes,
        )

    async def get_user_mfa_settings(self, user_id: UUID) -> Optional[MFASettings]:
        """Get MFA settings for a user."""
        result = await self.db.execute(
            select(MFASettings)
            .where(MFASettings.user_id == user_id)
            .options(selectinload(MFASettings.recovery_codes))
        )
        return result.scalar_one_or_none()

    async def get_or_create_mfa_settings(self, user_id: UUID) -> MFASettings:
        """Get or create MFA settings for a user."""
        settings = await self.get_user_mfa_settings(user_id)

        if settings is None:
            settings = MFASettings(
                user_id=user_id,
                enabled=False,
                remember_device_days=self.mfa_policy.remember_device_days,
            )
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings

    async def setup_totp(self, user_id: UUID) -> Tuple[str, str]:
        """
        Initialize TOTP setup for a user.

        Returns:
            Tuple of (secret, provisioning_uri)
        """
        settings = await self.get_or_create_mfa_settings(user_id)

        secret = self.manager.generate_totp_secret()

        user_email = f"user_{user_id}"
        provisioning_uri = self.manager.get_totp_provisioning_uri(
            secret=secret,
            account_name=user_email,
        )

        settings.totp_secret = secret
        settings.totp_enabled = False
        settings.totp_verified = False

        await self.db.commit()

        logger.info(f"TOTP setup initiated for user {user_id}")

        return secret, provisioning_uri

    async def verify_and_enable_totp(
        self,
        user_id: UUID,
        code: str,
    ) -> MFAVerificationResult:
        """Verify TOTP code and enable TOTP for the user."""
        settings = await self.get_user_mfa_settings(user_id)

        if settings is None or not settings.totp_secret:
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.TOTP,
                message="TOTP not configured. Please start setup first.",
            )

        if self.manager.verify_totp(settings.totp_secret, code):
            settings.totp_enabled = True
            settings.totp_verified = True
            settings.totp_verified_at = utc_now()
            settings.enabled = True
            settings.primary_method = MFAMethodType.TOTP

            await self.db.commit()

            logger.info(f"TOTP enabled for user {user_id}")

            return MFAVerificationResult(
                success=True,
                method=MFAMethod.TOTP,
                message="TOTP successfully enabled",
            )

        return MFAVerificationResult(
            success=False,
            method=MFAMethod.TOTP,
            message="Invalid verification code",
        )

    async def setup_sms(self, user_id: UUID, phone_number: str) -> Tuple[str, datetime]:
        """
        Initialize SMS MFA setup.

        Returns:
            Tuple of (code, expires_at)
        """
        settings = await self.get_or_create_mfa_settings(user_id)

        settings.sms_phone_number = phone_number
        settings.sms_verified = False

        code, expires_at = self.manager.generate_sms_code(str(user_id), phone_number)

        await self.db.commit()

        logger.info(f"SMS setup initiated for user {user_id}")

        return code, expires_at

    async def verify_and_enable_sms(
        self,
        user_id: UUID,
        code: str,
    ) -> MFAVerificationResult:
        """Verify SMS code and enable SMS MFA."""
        settings = await self.get_user_mfa_settings(user_id)

        if settings is None or not settings.sms_phone_number:
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.SMS,
                message="SMS not configured. Please start setup first.",
            )

        result = self.manager.verify_sms_code(str(user_id), code)

        if result.success:
            settings.sms_enabled = True
            settings.sms_verified = True
            settings.sms_verified_at = utc_now()
            settings.enabled = True

            if not settings.primary_method:
                settings.primary_method = MFAMethodType.SMS

            await self.db.commit()

            logger.info(f"SMS MFA enabled for user {user_id}")

        return result

    async def setup_email(self, user_id: UUID, email: str) -> Tuple[str, datetime]:
        """
        Initialize email MFA setup.

        Returns:
            Tuple of (code, expires_at)
        """
        settings = await self.get_or_create_mfa_settings(user_id)

        settings.email_address = email
        settings.email_verified = False

        code, expires_at = self.manager.generate_email_code(str(user_id), email)

        await self.db.commit()

        logger.info(f"Email MFA setup initiated for user {user_id}")

        return code, expires_at

    async def verify_and_enable_email(
        self,
        user_id: UUID,
        code: str,
    ) -> MFAVerificationResult:
        """Verify email code and enable email MFA."""
        settings = await self.get_user_mfa_settings(user_id)

        if settings is None or not settings.email_address:
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.EMAIL,
                message="Email MFA not configured. Please start setup first.",
            )

        result = self.manager.verify_email_code(str(user_id), code)

        if result.success:
            settings.email_enabled = True
            settings.email_verified = True
            settings.email_verified_at = utc_now()
            settings.enabled = True

            if not settings.primary_method:
                settings.primary_method = MFAMethodType.EMAIL

            await self.db.commit()

            logger.info(f"Email MFA enabled for user {user_id}")

        return result

    async def generate_recovery_codes(
        self,
        user_id: UUID,
        regenerate: bool = False,
    ) -> List[str]:
        """Generate recovery codes for a user."""
        settings = await self.get_user_mfa_settings(user_id)

        if settings is None:
            raise ValueError("MFA not configured for user")

        if regenerate:
            await self.db.execute(
                delete(MFARecoveryCode).where(
                    MFARecoveryCode.mfa_settings_id == settings.id
                )
            )

        codes = self.manager.generate_recovery_codes(
            count=self.mfa_policy.recovery_codes_count,
            length=self.mfa_policy.recovery_code_length,
        )

        for code in codes:
            code_hash = self.manager.hash_recovery_code(code)
            recovery_code = MFARecoveryCode(
                mfa_settings_id=settings.id,
                code_hash=code_hash,
            )
            self.db.add(recovery_code)

        settings.recovery_codes_generated = True
        settings.recovery_codes_generated_at = utc_now()
        settings.recovery_codes_remaining = len(codes)

        await self.db.commit()

        logger.info(f"Generated {len(codes)} recovery codes for user {user_id}")

        return codes

    async def verify_mfa(
        self,
        user_id: UUID,
        method: MFAMethod,
        code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MFAVerificationResult:
        """
        Verify MFA code for login.

        Args:
            user_id: The user ID
            method: The MFA method being used
            code: The verification code
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            MFAVerificationResult
        """
        settings = await self.get_user_mfa_settings(user_id)

        if settings is None or not settings.enabled:
            return MFAVerificationResult(
                success=False,
                method=method,
                message="MFA not enabled for this user",
            )

        if settings.is_locked():
            return MFAVerificationResult(
                success=False,
                method=method,
                message="Account temporarily locked due to too many failed attempts",
                lockout_until=settings.locked_until,
            )

        result = None

        if method == MFAMethod.TOTP:
            if not settings.totp_enabled:
                return MFAVerificationResult(
                    success=False,
                    method=method,
                    message="TOTP not enabled",
                )

            success = self.manager.verify_totp(settings.totp_secret, code)
            result = MFAVerificationResult(
                success=success,
                method=method,
                message="Verification successful" if success else "Invalid code",
            )

        elif method == MFAMethod.SMS:
            result = self.manager.verify_sms_code(str(user_id), code)

        elif method == MFAMethod.EMAIL:
            result = self.manager.verify_email_code(str(user_id), code)

        elif method == MFAMethod.BACKUP_CODE:
            result = await self._verify_recovery_code(
                settings, code, ip_address, user_agent
            )

        else:
            result = MFAVerificationResult(
                success=False,
                method=method,
                message=f"Unsupported MFA method: {method}",
            )

        if result.success:
            settings.record_successful_verification(MFAMethodType(method.value))
        else:
            settings.increment_failed_attempts(
                max_attempts=self.mfa_policy.max_verification_attempts,
                lockout_minutes=self.mfa_policy.lockout_duration_minutes,
            )

        await self.db.commit()

        return result

    async def _verify_recovery_code(
        self,
        settings: MFASettings,
        code: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> MFAVerificationResult:
        """Verify a recovery code."""
        result = await self.db.execute(
            select(MFARecoveryCode).where(
                MFARecoveryCode.mfa_settings_id == settings.id,
                MFARecoveryCode.used == False,
            )
        )
        recovery_codes = result.scalars().all()

        if not recovery_codes:
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.BACKUP_CODE,
                message="No recovery codes available",
            )

        code_hash = self.manager.hash_recovery_code(code)

        for rc in recovery_codes:
            if rc.code_hash == code_hash:
                rc.mark_used(ip_address, user_agent)
                settings.recovery_codes_remaining -= 1

                await self.db.commit()

                logger.warning(
                    f"Recovery code used for user {settings.user_id}. "
                    f"Remaining: {settings.recovery_codes_remaining}"
                )

                return MFAVerificationResult(
                    success=True,
                    method=MFAMethod.BACKUP_CODE,
                    message="Recovery code accepted",
                    recovery_code_used=True,
                )

        return MFAVerificationResult(
            success=False,
            method=MFAMethod.BACKUP_CODE,
            message="Invalid recovery code",
        )

    async def create_challenge(
        self,
        user_id: UUID,
        method: MFAMethod,
        purpose: str = "login",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> MFAChallenge:
        """Create an MFA challenge for verification."""
        settings = await self.get_user_mfa_settings(user_id)

        if settings is None:
            raise ValueError("MFA not configured for user")

        if method == MFAMethod.SMS:
            expiry_minutes = self.mfa_policy.sms_code_expiry_minutes
        elif method == MFAMethod.EMAIL:
            expiry_minutes = self.mfa_policy.email_code_expiry_minutes
        else:
            expiry_minutes = 5

        challenge = MFAChallenge(
            mfa_settings_id=settings.id,
            method=MFAMethodType(method.value),
            expires_at=utc_now() + timedelta(minutes=expiry_minutes),
            ip_address=ip_address,
            user_agent=user_agent[:512] if user_agent else None,
            session_id=session_id,
            purpose=purpose,
            max_attempts=self.mfa_policy.max_verification_attempts,
        )

        self.db.add(challenge)
        await self.db.commit()
        await self.db.refresh(challenge)

        return challenge

    async def trust_device(
        self,
        user_id: UUID,
        device_token: str,
        device_name: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> TrustedDevice:
        """Add a device to the trusted devices list."""
        import hashlib

        token_hash = hashlib.sha256(device_token.encode()).hexdigest()

        expires_at = utc_now() + timedelta(
            days=self.mfa_policy.remember_device_days
        )

        device = TrustedDevice(
            user_id=user_id,
            device_token_hash=token_hash,
            device_name=device_name,
            device_type=device_info.get("device_type") if device_info else None,
            browser=device_info.get("browser") if device_info else None,
            browser_version=device_info.get("browser_version") if device_info else None,
            os_name=device_info.get("os_name") if device_info else None,
            os_version=device_info.get("os_version") if device_info else None,
            ip_address=ip_address,
            expires_at=expires_at,
        )

        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)

        logger.info(f"Device trusted for user {user_id}")

        return device

    async def verify_trusted_device(
        self,
        user_id: UUID,
        device_token: str,
    ) -> bool:
        """Check if a device is trusted."""
        import hashlib

        token_hash = hashlib.sha256(device_token.encode()).hexdigest()

        result = await self.db.execute(
            select(TrustedDevice).where(
                TrustedDevice.user_id == user_id,
                TrustedDevice.device_token_hash == token_hash,
                TrustedDevice.is_active == True,
            )
        )
        device = result.scalar_one_or_none()

        if device and device.is_valid():
            device.record_use()
            await self.db.commit()
            return True

        return False

    async def revoke_trusted_device(
        self,
        user_id: UUID,
        device_id: UUID,
        reason: Optional[str] = None,
    ) -> bool:
        """Revoke a trusted device."""
        result = await self.db.execute(
            select(TrustedDevice).where(
                TrustedDevice.id == device_id,
                TrustedDevice.user_id == user_id,
            )
        )
        device = result.scalar_one_or_none()

        if device:
            device.revoke(reason)
            await self.db.commit()
            logger.info(f"Device {device_id} revoked for user {user_id}")
            return True

        return False

    async def get_trusted_devices(self, user_id: UUID) -> List[TrustedDevice]:
        """Get all trusted devices for a user."""
        result = await self.db.execute(
            select(TrustedDevice).where(
                TrustedDevice.user_id == user_id,
                TrustedDevice.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def disable_mfa(self, user_id: UUID) -> bool:
        """Disable MFA for a user."""
        settings = await self.get_user_mfa_settings(user_id)

        if settings is None:
            return False

        settings.enabled = False
        settings.totp_enabled = False
        settings.totp_secret = None
        settings.totp_verified = False
        settings.sms_enabled = False
        settings.sms_verified = False
        settings.email_enabled = False
        settings.email_verified = False

        await self.db.execute(
            delete(MFARecoveryCode).where(
                MFARecoveryCode.mfa_settings_id == settings.id
            )
        )

        settings.recovery_codes_generated = False
        settings.recovery_codes_remaining = 0

        await self.db.commit()

        logger.info(f"MFA disabled for user {user_id}")

        return True

    async def is_mfa_required(self, user_id: UUID, is_admin: bool = False) -> bool:
        """Check if MFA is required for a user."""
        if self.mfa_policy.required_for_all:
            return True

        if is_admin and self.mfa_policy.required_for_admins:
            return True

        settings = await self.get_user_mfa_settings(user_id)

        return settings is not None and settings.enabled


_mfa_service: Optional[MFAService] = None


def get_mfa_service(db: AsyncSession) -> MFAService:
    """Get MFA service instance."""
    return MFAService(db)
