"""
AES-256-GCM encryption implementation for LogiAccounting Pro.
"""

import os
import base64
import struct
from typing import Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.utils.datetime_utils import utc_now


NONCE_SIZE = 12
TAG_SIZE = 16
KEY_SIZE = 32
SALT_SIZE = 16
VERSION_SIZE = 1
CURRENT_VERSION = 1


@dataclass
class EncryptionMetadata:
    """Metadata associated with encrypted data."""

    version: int
    key_id: str
    algorithm: str
    encrypted_at: datetime
    nonce: bytes
    associated_data: Optional[bytes] = None


class AESCipher:
    """AES-256-GCM cipher implementation."""

    def __init__(
        self,
        key: Optional[bytes] = None,
        key_id: str = "default",
    ):
        self._key_id = key_id
        if key:
            if len(key) != KEY_SIZE:
                raise ValueError(f"Key must be {KEY_SIZE} bytes for AES-256")
            self._key = key
        else:
            self._key = self._generate_key()
        self._cipher = AESGCM(self._key)

    @staticmethod
    def _generate_key() -> bytes:
        """Generate a cryptographically secure random key."""
        return os.urandom(KEY_SIZE)

    @staticmethod
    def generate_nonce() -> bytes:
        """Generate a cryptographically secure random nonce."""
        return os.urandom(NONCE_SIZE)

    @staticmethod
    def derive_key(
        password: str,
        salt: Optional[bytes] = None,
        iterations: int = 100000,
    ) -> Tuple[bytes, bytes]:
        """Derive an encryption key from a password using PBKDF2."""
        if salt is None:
            salt = os.urandom(SALT_SIZE)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=iterations,
            backend=default_backend(),
        )

        key = kdf.derive(password.encode("utf-8"))
        return key, salt

    def encrypt(
        self,
        plaintext: Union[str, bytes],
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Encrypt data using AES-256-GCM.

        Format: version (1 byte) + nonce (12 bytes) + ciphertext + tag (16 bytes)
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        nonce = self.generate_nonce()
        ciphertext = self._cipher.encrypt(nonce, plaintext, associated_data)

        version_byte = struct.pack("B", CURRENT_VERSION)
        return version_byte + nonce + ciphertext

    def decrypt(
        self,
        ciphertext: bytes,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt data encrypted with AES-256-GCM.

        Expects format: version (1 byte) + nonce (12 bytes) + ciphertext + tag
        """
        if len(ciphertext) < VERSION_SIZE + NONCE_SIZE + TAG_SIZE:
            raise ValueError("Invalid ciphertext: too short")

        version = struct.unpack("B", ciphertext[:VERSION_SIZE])[0]
        if version != CURRENT_VERSION:
            raise ValueError(f"Unsupported encryption version: {version}")

        nonce = ciphertext[VERSION_SIZE:VERSION_SIZE + NONCE_SIZE]
        encrypted_data = ciphertext[VERSION_SIZE + NONCE_SIZE:]

        return self._cipher.decrypt(nonce, encrypted_data, associated_data)

    def encrypt_to_base64(
        self,
        plaintext: Union[str, bytes],
        associated_data: Optional[bytes] = None,
    ) -> str:
        """Encrypt and return base64-encoded result."""
        encrypted = self.encrypt(plaintext, associated_data)
        return base64.b64encode(encrypted).decode("ascii")

    def decrypt_from_base64(
        self,
        ciphertext_b64: str,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Decrypt base64-encoded ciphertext."""
        ciphertext = base64.b64decode(ciphertext_b64)
        return self.decrypt(ciphertext, associated_data)

    def encrypt_string(
        self,
        plaintext: str,
        associated_data: Optional[bytes] = None,
    ) -> str:
        """Encrypt a string and return base64-encoded result."""
        return self.encrypt_to_base64(plaintext, associated_data)

    def decrypt_string(
        self,
        ciphertext_b64: str,
        associated_data: Optional[bytes] = None,
    ) -> str:
        """Decrypt base64-encoded ciphertext and return string."""
        decrypted = self.decrypt_from_base64(ciphertext_b64, associated_data)
        return decrypted.decode("utf-8")

    def encrypt_with_metadata(
        self,
        plaintext: Union[str, bytes],
        associated_data: Optional[bytes] = None,
    ) -> Tuple[bytes, EncryptionMetadata]:
        """Encrypt data and return metadata separately."""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        nonce = self.generate_nonce()
        ciphertext = self._cipher.encrypt(nonce, plaintext, associated_data)

        metadata = EncryptionMetadata(
            version=CURRENT_VERSION,
            key_id=self._key_id,
            algorithm="AES-256-GCM",
            encrypted_at=utc_now(),
            nonce=nonce,
            associated_data=associated_data,
        )

        return ciphertext, metadata

    def decrypt_with_metadata(
        self,
        ciphertext: bytes,
        metadata: EncryptionMetadata,
    ) -> bytes:
        """Decrypt data using provided metadata."""
        return self._cipher.decrypt(
            metadata.nonce,
            ciphertext,
            metadata.associated_data,
        )

    @property
    def key_id(self) -> str:
        """Get the key identifier."""
        return self._key_id

    def rotate_key(self, new_key: Optional[bytes] = None) -> "AESCipher":
        """Create a new cipher with a rotated key."""
        return AESCipher(
            key=new_key,
            key_id=f"{self._key_id}_rotated_{utc_now().strftime('%Y%m%d')}",
        )


class PasswordBasedCipher:
    """Password-based encryption using PBKDF2 key derivation."""

    def __init__(self, password: str, iterations: int = 100000):
        self._password = password
        self._iterations = iterations

    def encrypt(
        self,
        plaintext: Union[str, bytes],
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Encrypt data using password-derived key.

        Format: version (1 byte) + salt (16 bytes) + nonce (12 bytes) + ciphertext + tag
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        key, salt = AESCipher.derive_key(self._password, iterations=self._iterations)
        cipher = AESGCM(key)
        nonce = AESCipher.generate_nonce()
        ciphertext = cipher.encrypt(nonce, plaintext, associated_data)

        version_byte = struct.pack("B", CURRENT_VERSION)
        return version_byte + salt + nonce + ciphertext

    def decrypt(
        self,
        ciphertext: bytes,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Decrypt password-encrypted data."""
        min_length = VERSION_SIZE + SALT_SIZE + NONCE_SIZE + TAG_SIZE
        if len(ciphertext) < min_length:
            raise ValueError("Invalid ciphertext: too short")

        version = struct.unpack("B", ciphertext[:VERSION_SIZE])[0]
        if version != CURRENT_VERSION:
            raise ValueError(f"Unsupported encryption version: {version}")

        salt = ciphertext[VERSION_SIZE:VERSION_SIZE + SALT_SIZE]
        nonce = ciphertext[VERSION_SIZE + SALT_SIZE:VERSION_SIZE + SALT_SIZE + NONCE_SIZE]
        encrypted_data = ciphertext[VERSION_SIZE + SALT_SIZE + NONCE_SIZE:]

        key, _ = AESCipher.derive_key(
            self._password,
            salt=salt,
            iterations=self._iterations,
        )
        cipher = AESGCM(key)

        return cipher.decrypt(nonce, encrypted_data, associated_data)

    def encrypt_to_base64(
        self,
        plaintext: Union[str, bytes],
        associated_data: Optional[bytes] = None,
    ) -> str:
        """Encrypt and return base64-encoded result."""
        encrypted = self.encrypt(plaintext, associated_data)
        return base64.b64encode(encrypted).decode("ascii")

    def decrypt_from_base64(
        self,
        ciphertext_b64: str,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Decrypt base64-encoded ciphertext."""
        ciphertext = base64.b64decode(ciphertext_b64)
        return self.decrypt(ciphertext, associated_data)


def create_cipher(key: Optional[bytes] = None, key_id: str = "default") -> AESCipher:
    """Factory function to create an AES cipher."""
    return AESCipher(key=key, key_id=key_id)


def create_password_cipher(password: str, iterations: int = 100000) -> PasswordBasedCipher:
    """Factory function to create a password-based cipher."""
    return PasswordBasedCipher(password=password, iterations=iterations)
