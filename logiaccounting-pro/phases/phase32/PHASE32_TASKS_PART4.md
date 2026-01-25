# Phase 32: Advanced Security - Part 4: Encryption & Key Management

## Overview
This part covers data encryption at rest, field-level encryption, and key management.

---

## File 1: AES Encryption
**Path:** `backend/app/security/encryption/aes.py`

```python
"""
AES Encryption
AES-256-GCM encryption for data at rest
"""

from typing import Optional, Tuple
import os
import base64
import secrets
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class AESCipher:
    """AES-256-GCM cipher for encryption/decryption."""
    
    # AES-256 requires 32-byte key
    KEY_SIZE = 32
    # GCM nonce size (96 bits recommended)
    NONCE_SIZE = 12
    # GCM tag size
    TAG_SIZE = 16
    
    def __init__(self, key: bytes = None):
        """Initialize cipher with key."""
        if key:
            if len(key) != self.KEY_SIZE:
                raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
            self._key = key
        else:
            self._key = None
    
    @classmethod
    def generate_key(cls) -> bytes:
        """Generate a new encryption key."""
        return secrets.token_bytes(cls.KEY_SIZE)
    
    @classmethod
    def key_from_password(cls, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Derive key from password using PBKDF2."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=cls.KEY_SIZE,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        
        key = kdf.derive(password.encode())
        return key, salt
    
    def encrypt(self, plaintext: bytes, associated_data: bytes = None) -> bytes:
        """
        Encrypt data using AES-256-GCM.
        Returns: nonce + ciphertext + tag
        """
        if not self._key:
            raise ValueError("No encryption key set")
        
        nonce = secrets.token_bytes(self.NONCE_SIZE)
        aesgcm = AESGCM(self._key)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
        
        # Return nonce + ciphertext (tag is appended by GCM)
        return nonce + ciphertext
    
    def decrypt(self, ciphertext: bytes, associated_data: bytes = None) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        Input: nonce + ciphertext + tag
        """
        if not self._key:
            raise ValueError("No encryption key set")
        
        if len(ciphertext) < self.NONCE_SIZE + self.TAG_SIZE:
            raise ValueError("Ciphertext too short")
        
        nonce = ciphertext[:self.NONCE_SIZE]
        actual_ciphertext = ciphertext[self.NONCE_SIZE:]
        
        aesgcm = AESGCM(self._key)
        
        try:
            plaintext = aesgcm.decrypt(nonce, actual_ciphertext, associated_data)
            return plaintext
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - data may be corrupted or key is incorrect")
    
    def encrypt_string(self, plaintext: str, encoding: str = "utf-8") -> str:
        """Encrypt a string and return base64-encoded result."""
        encrypted = self.encrypt(plaintext.encode(encoding))
        return base64.b64encode(encrypted).decode("ascii")
    
    def decrypt_string(self, ciphertext: str, encoding: str = "utf-8") -> str:
        """Decrypt a base64-encoded string."""
        encrypted = base64.b64decode(ciphertext.encode("ascii"))
        decrypted = self.decrypt(encrypted)
        return decrypted.decode(encoding)


class EncryptionService:
    """High-level encryption service."""
    
    def __init__(self):
        self._cipher: Optional[AESCipher] = None
        self._key_id: Optional[str] = None
        self._init_from_env()
    
    def _init_from_env(self):
        """Initialize from environment variables."""
        from app.security.config import get_security_config
        
        config = get_security_config()
        key_str = config.encryption_key
        
        if key_str:
            try:
                key = base64.b64decode(key_str)
                self._cipher = AESCipher(key)
                self._key_id = "env_key"
                logger.info("Encryption service initialized from environment")
            except Exception as e:
                logger.warning(f"Failed to initialize encryption from env: {e}")
    
    @property
    def is_available(self) -> bool:
        """Check if encryption is available."""
        return self._cipher is not None
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt binary data."""
        if not self._cipher:
            raise RuntimeError("Encryption not configured")
        return self._cipher.encrypt(data)
    
    def decrypt(self, data: bytes) -> bytes:
        """Decrypt binary data."""
        if not self._cipher:
            raise RuntimeError("Encryption not configured")
        return self._cipher.decrypt(data)
    
    def encrypt_string(self, plaintext: str) -> str:
        """Encrypt a string."""
        if not self._cipher:
            raise RuntimeError("Encryption not configured")
        return self._cipher.encrypt_string(plaintext)
    
    def decrypt_string(self, ciphertext: str) -> str:
        """Decrypt a string."""
        if not self._cipher:
            raise RuntimeError("Encryption not configured")
        return self._cipher.decrypt_string(ciphertext)
    
    def set_key(self, key: bytes, key_id: str = None):
        """Set encryption key."""
        self._cipher = AESCipher(key)
        self._key_id = key_id or "manual_key"


# Global encryption service
encryption_service = EncryptionService()


def get_encryption_service() -> EncryptionService:
    """Get encryption service instance."""
    return encryption_service
```

---

## File 2: Field-Level Encryption
**Path:** `backend/app/security/encryption/fields.py`

```python
"""
Field-Level Encryption
Encrypt sensitive fields in database
"""

from typing import Any, Optional, Type, List
from functools import wraps
import logging

from app.security.encryption.aes import encryption_service

logger = logging.getLogger(__name__)


# Fields that should be encrypted
ENCRYPTED_FIELDS = {
    "credit_card_number",
    "bank_account_number",
    "routing_number",
    "ssn",
    "tax_id",
    "phone_number",
    "address",
    "totp_secret",
}

# Fields that contain PII
PII_FIELDS = {
    "email",
    "phone_number",
    "address",
    "first_name",
    "last_name",
    "date_of_birth",
    "ssn",
    "tax_id",
}

# Fields that contain financial data
FINANCIAL_FIELDS = {
    "credit_card_number",
    "bank_account_number",
    "routing_number",
    "amount",
    "balance",
}


def encrypt_field(value: str) -> str:
    """
    Encrypt a field value.
    Returns encrypted string or original if encryption unavailable.
    """
    if not value:
        return value
    
    if not encryption_service.is_available:
        logger.warning("Encryption not available - storing plaintext")
        return value
    
    try:
        encrypted = encryption_service.encrypt_string(value)
        return f"enc:{encrypted}"
    except Exception as e:
        logger.error(f"Field encryption failed: {e}")
        return value


def decrypt_field(value: str) -> str:
    """
    Decrypt a field value.
    Returns decrypted string or original if not encrypted.
    """
    if not value:
        return value
    
    if not value.startswith("enc:"):
        return value
    
    if not encryption_service.is_available:
        logger.error("Cannot decrypt - encryption not available")
        return value
    
    try:
        encrypted = value[4:]  # Remove "enc:" prefix
        return encryption_service.decrypt_string(encrypted)
    except Exception as e:
        logger.error(f"Field decryption failed: {e}")
        return value


def is_encrypted(value: str) -> bool:
    """Check if a value is encrypted."""
    return value.startswith("enc:") if value else False


def should_encrypt_field(field_name: str) -> bool:
    """Check if a field should be encrypted."""
    from app.security.config import get_security_config
    
    config = get_security_config().encryption_policy
    
    if field_name in ENCRYPTED_FIELDS:
        return True
    
    if config.encrypt_pii and field_name in PII_FIELDS:
        return True
    
    if config.encrypt_financial and field_name in FINANCIAL_FIELDS:
        return True
    
    return False


class EncryptedField:
    """
    Descriptor for encrypted model fields.
    Use as a property-like accessor on SQLAlchemy models.
    """
    
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.encrypted_field_name = f"_{field_name}_encrypted"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        encrypted_value = getattr(obj, self.encrypted_field_name, None)
        if encrypted_value:
            return decrypt_field(encrypted_value)
        return None
    
    def __set__(self, obj, value):
        if value:
            encrypted_value = encrypt_field(value)
        else:
            encrypted_value = None
        setattr(obj, self.encrypted_field_name, encrypted_value)


def encrypt_dict_fields(data: dict, fields: List[str] = None) -> dict:
    """
    Encrypt specified fields in a dictionary.
    If fields not specified, encrypts all known sensitive fields.
    """
    result = data.copy()
    fields_to_encrypt = fields or list(ENCRYPTED_FIELDS | PII_FIELDS | FINANCIAL_FIELDS)
    
    for field in fields_to_encrypt:
        if field in result and result[field]:
            result[field] = encrypt_field(str(result[field]))
    
    return result


def decrypt_dict_fields(data: dict, fields: List[str] = None) -> dict:
    """
    Decrypt specified fields in a dictionary.
    If fields not specified, decrypts all potentially encrypted fields.
    """
    result = data.copy()
    fields_to_decrypt = fields or list(ENCRYPTED_FIELDS | PII_FIELDS | FINANCIAL_FIELDS)
    
    for field in fields_to_decrypt:
        if field in result and result[field]:
            result[field] = decrypt_field(str(result[field]))
    
    return result


def mask_field(value: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """
    Mask a field value, showing only last N characters.
    Useful for displaying encrypted/sensitive data.
    """
    if not value:
        return ""
    
    if len(value) <= visible_chars:
        return mask_char * len(value)
    
    masked_length = len(value) - visible_chars
    return (mask_char * masked_length) + value[-visible_chars:]


def mask_email(email: str) -> str:
    """Mask an email address."""
    if not email or "@" not in email:
        return email
    
    local, domain = email.split("@", 1)
    
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask a phone number."""
    if not phone:
        return ""
    
    # Keep only digits
    digits = "".join(filter(str.isdigit, phone))
    
    if len(digits) <= 4:
        return "*" * len(digits)
    
    return "*" * (len(digits) - 4) + digits[-4:]


class FieldMasker:
    """Utility for masking sensitive data in responses."""
    
    MASKING_RULES = {
        "credit_card_number": lambda v: mask_field(v, 4),
        "bank_account_number": lambda v: mask_field(v, 4),
        "ssn": lambda v: mask_field(v, 4),
        "tax_id": lambda v: mask_field(v, 4),
        "phone_number": mask_phone,
        "email": mask_email,
        "routing_number": lambda v: mask_field(v, 4),
    }
    
    @classmethod
    def mask_dict(cls, data: dict, fields: List[str] = None) -> dict:
        """Mask sensitive fields in a dictionary."""
        result = data.copy()
        fields_to_mask = fields or list(cls.MASKING_RULES.keys())
        
        for field in fields_to_mask:
            if field in result and result[field]:
                masker = cls.MASKING_RULES.get(field, lambda v: mask_field(v, 4))
                result[field] = masker(str(result[field]))
        
        return result
```

---

## File 3: Key Management
**Path:** `backend/app/security/encryption/keys.py`

```python
"""
Key Management
Encryption key lifecycle management
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import secrets
import base64
import logging
from uuid import uuid4

from app.security.encryption.aes import AESCipher

logger = logging.getLogger(__name__)


class KeyStatus(str, Enum):
    """Key status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_ROTATION = "pending_rotation"
    RETIRED = "retired"


class KeyType(str, Enum):
    """Key types."""
    MASTER = "master"
    DATA = "data"
    SESSION = "session"
    SIGNING = "signing"


@dataclass
class EncryptionKey:
    """Encryption key metadata."""
    id: str
    key_type: KeyType
    version: int
    status: KeyStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    rotated_by: Optional[str] = None
    algorithm: str = "AES-256-GCM"
    
    # Key material (encrypted in production)
    _key_material: Optional[bytes] = field(default=None, repr=False)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "key_type": self.key_type.value,
            "version": self.version,
            "status": self.status.value,
            "algorithm": self.algorithm,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
        }


class KeyManager:
    """Manages encryption keys."""
    
    DEFAULT_KEY_TTL_DAYS = 90
    
    def __init__(self):
        self._keys: Dict[str, EncryptionKey] = {}
        self._active_keys: Dict[KeyType, str] = {}  # type -> key_id
    
    def generate_key(
        self,
        key_type: KeyType,
        ttl_days: int = None,
    ) -> EncryptionKey:
        """Generate a new encryption key."""
        ttl = ttl_days or self.DEFAULT_KEY_TTL_DAYS
        
        # Get next version for this key type
        existing = [k for k in self._keys.values() if k.key_type == key_type]
        version = max([k.version for k in existing], default=0) + 1
        
        key = EncryptionKey(
            id=f"key_{uuid4().hex[:12]}",
            key_type=key_type,
            version=version,
            status=KeyStatus.ACTIVE,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=ttl),
            _key_material=AESCipher.generate_key(),
        )
        
        self._keys[key.id] = key
        self._active_keys[key_type] = key.id
        
        logger.info(f"Generated new {key_type.value} key: {key.id} (version {version})")
        return key
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get key by ID."""
        return self._keys.get(key_id)
    
    def get_active_key(self, key_type: KeyType) -> Optional[EncryptionKey]:
        """Get active key for a type."""
        key_id = self._active_keys.get(key_type)
        if key_id:
            return self._keys.get(key_id)
        return None
    
    def get_key_material(self, key_id: str) -> Optional[bytes]:
        """Get key material (the actual key bytes)."""
        key = self._keys.get(key_id)
        if key and key.status == KeyStatus.ACTIVE:
            return key._key_material
        return None
    
    def rotate_key(
        self,
        key_type: KeyType,
        rotated_by: str = None,
    ) -> EncryptionKey:
        """Rotate a key (create new, mark old for retirement)."""
        old_key_id = self._active_keys.get(key_type)
        
        # Mark old key for rotation
        if old_key_id:
            old_key = self._keys.get(old_key_id)
            if old_key:
                old_key.status = KeyStatus.PENDING_ROTATION
                old_key.rotated_at = datetime.utcnow()
                old_key.rotated_by = rotated_by
        
        # Generate new key
        new_key = self.generate_key(key_type)
        new_key.rotated_by = rotated_by
        
        logger.info(f"Rotated {key_type.value} key from {old_key_id} to {new_key.id}")
        return new_key
    
    def retire_key(self, key_id: str):
        """Retire a key (can no longer be used for encryption)."""
        key = self._keys.get(key_id)
        if key:
            key.status = KeyStatus.RETIRED
            
            # Remove from active if it was active
            for key_type, active_id in list(self._active_keys.items()):
                if active_id == key_id:
                    del self._active_keys[key_type]
            
            logger.info(f"Retired key: {key_id}")
    
    def list_keys(
        self,
        key_type: KeyType = None,
        status: KeyStatus = None,
    ) -> List[EncryptionKey]:
        """List keys with optional filters."""
        keys = list(self._keys.values())
        
        if key_type:
            keys = [k for k in keys if k.key_type == key_type]
        
        if status:
            keys = [k for k in keys if k.status == status]
        
        return sorted(keys, key=lambda k: k.version, reverse=True)
    
    def check_expiring_keys(self, days_ahead: int = 7) -> List[EncryptionKey]:
        """Find keys expiring soon."""
        threshold = datetime.utcnow() + timedelta(days=days_ahead)
        
        expiring = [
            k for k in self._keys.values()
            if k.status == KeyStatus.ACTIVE
            and k.expires_at
            and k.expires_at <= threshold
        ]
        
        return expiring
    
    def export_key_metadata(self) -> Dict:
        """Export key metadata (not key material)."""
        return {
            "keys": [k.to_dict() for k in self._keys.values()],
            "active_keys": {
                kt.value: kid for kt, kid in self._active_keys.items()
            },
        }


# Global key manager
key_manager = KeyManager()


def get_key_manager() -> KeyManager:
    """Get key manager instance."""
    return key_manager


def init_encryption_keys():
    """Initialize encryption keys on startup."""
    # Generate master key if none exists
    if not key_manager.get_active_key(KeyType.MASTER):
        key_manager.generate_key(KeyType.MASTER)
    
    # Generate data key if none exists
    if not key_manager.get_active_key(KeyType.DATA):
        key_manager.generate_key(KeyType.DATA)
    
    logger.info("Encryption keys initialized")
```

---

## File 4: Encryption Module Init
**Path:** `backend/app/security/encryption/__init__.py`

```python
"""
Encryption Module
Data encryption and key management
"""

from app.security.encryption.aes import (
    AESCipher,
    EncryptionService,
    encryption_service,
    get_encryption_service,
)

from app.security.encryption.fields import (
    encrypt_field,
    decrypt_field,
    is_encrypted,
    should_encrypt_field,
    EncryptedField,
    encrypt_dict_fields,
    decrypt_dict_fields,
    mask_field,
    mask_email,
    mask_phone,
    FieldMasker,
    ENCRYPTED_FIELDS,
    PII_FIELDS,
    FINANCIAL_FIELDS,
)

from app.security.encryption.keys import (
    KeyManager,
    EncryptionKey,
    KeyStatus,
    KeyType,
    key_manager,
    get_key_manager,
    init_encryption_keys,
)


__all__ = [
    # AES
    'AESCipher',
    'EncryptionService',
    'encryption_service',
    'get_encryption_service',
    
    # Fields
    'encrypt_field',
    'decrypt_field',
    'is_encrypted',
    'should_encrypt_field',
    'EncryptedField',
    'encrypt_dict_fields',
    'decrypt_dict_fields',
    'mask_field',
    'mask_email',
    'mask_phone',
    'FieldMasker',
    'ENCRYPTED_FIELDS',
    'PII_FIELDS',
    'FINANCIAL_FIELDS',
    
    # Keys
    'KeyManager',
    'EncryptionKey',
    'KeyStatus',
    'KeyType',
    'key_manager',
    'get_key_manager',
    'init_encryption_keys',
]
```

---

## Summary Part 4

| File | Description | Lines |
|------|-------------|-------|
| `encryption/aes.py` | AES-256-GCM encryption | ~180 |
| `encryption/fields.py` | Field-level encryption | ~240 |
| `encryption/keys.py` | Key management | ~220 |
| `encryption/__init__.py` | Encryption module exports | ~65 |
| **Total** | | **~705 lines** |
