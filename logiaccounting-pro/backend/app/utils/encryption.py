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
        secret = os.getenv('SECRET_KEY', 'logiaccounting-secret-key-change-in-production-2024').encode()
        salt = os.getenv('ENCRYPTION_SALT', 'logiaccounting-sso-salt').encode()

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
