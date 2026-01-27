"""
Two-Factor Authentication Service
TOTP-based 2FA compatible with Google Authenticator, Authy, etc.
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Optional, List, Dict
from datetime import datetime


class TwoFactorService:
    """Manages 2FA for users"""

    _instance = None
    _user_2fa: Dict[str, dict] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._user_2fa = {}
        return cls._instance

    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for recovery"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes

    def hash_backup_code(self, code: str) -> str:
        """Hash a backup code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()

    def get_totp_uri(self, secret: str, email: str, issuer: str = "LogiAccounting") -> str:
        """Generate TOTP URI for QR code"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)

    def generate_qr_code(self, secret: str, email: str) -> str:
        """Generate QR code as base64 image"""
        uri = self.get_totp_uri(secret, email)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    def verify_code(self, secret: str, code: str) -> bool:
        """Verify a TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)

    def setup_2fa(self, user_id: str, email: str) -> dict:
        """Initialize 2FA setup for a user"""
        secret = self.generate_secret()
        backup_codes = self.generate_backup_codes()

        self._user_2fa[user_id] = {
            "secret": secret,
            "backup_codes": [self.hash_backup_code(c) for c in backup_codes],
            "backup_codes_plain": backup_codes,
            "enabled": False,
            "verified": False,
            "setup_at": datetime.utcnow().isoformat()
        }

        qr_code = self.generate_qr_code(secret, email)

        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes
        }

    def verify_setup(self, user_id: str, code: str) -> bool:
        """Verify 2FA setup with initial code"""
        if user_id not in self._user_2fa:
            return False

        user_2fa = self._user_2fa[user_id]

        if self.verify_code(user_2fa["secret"], code):
            user_2fa["verified"] = True
            user_2fa["enabled"] = True
            user_2fa["enabled_at"] = datetime.utcnow().isoformat()
            user_2fa.pop("backup_codes_plain", None)
            return True

        return False

    def verify_login(self, user_id: str, code: str) -> bool:
        """Verify 2FA code during login"""
        if user_id not in self._user_2fa:
            return False

        user_2fa = self._user_2fa[user_id]

        if not user_2fa.get("enabled"):
            return True

        if self.verify_code(user_2fa["secret"], code):
            return True

        code_hash = self.hash_backup_code(code)
        if code_hash in user_2fa["backup_codes"]:
            user_2fa["backup_codes"].remove(code_hash)
            return True

        return False

    def is_2fa_enabled(self, user_id: str) -> bool:
        """Check if user has 2FA enabled"""
        if user_id not in self._user_2fa:
            return False
        return self._user_2fa[user_id].get("enabled", False)

    def disable_2fa(self, user_id: str) -> bool:
        """Disable 2FA for a user"""
        if user_id in self._user_2fa:
            del self._user_2fa[user_id]
            return True
        return False

    def get_2fa_status(self, user_id: str) -> dict:
        """Get 2FA status for a user"""
        if user_id not in self._user_2fa:
            return {"enabled": False}

        user_2fa = self._user_2fa[user_id]
        return {
            "enabled": user_2fa.get("enabled", False),
            "verified": user_2fa.get("verified", False),
            "enabled_at": user_2fa.get("enabled_at"),
            "backup_codes_remaining": len(user_2fa.get("backup_codes", []))
        }


two_factor_service = TwoFactorService()
