"""
Field-level encryption for sensitive data in LogiAccounting Pro.
"""

import json
import hashlib
from typing import Optional, Any, Dict, List, Set, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from .aes import AESCipher, create_cipher
from .keys import KeyManager, get_key_manager


class FieldType(str, Enum):
    """Supported field types for encryption."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    BINARY = "binary"


@dataclass
class EncryptedFieldConfig:
    """Configuration for an encrypted field."""

    field_name: str
    field_type: FieldType = FieldType.STRING
    key_id: str = "default"
    searchable: bool = False
    deterministic: bool = False
    mask_format: Optional[str] = None
    audit_access: bool = True


class FieldEncryptor:
    """Handles encryption and decryption of individual fields."""

    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        default_key_id: str = "default",
    ):
        self._key_manager = key_manager or get_key_manager()
        self._default_key_id = default_key_id
        self._ciphers: Dict[str, AESCipher] = {}
        self._type_serializers: Dict[FieldType, callable] = {
            FieldType.STRING: str,
            FieldType.INTEGER: lambda x: str(int(x)),
            FieldType.FLOAT: lambda x: str(float(x)),
            FieldType.DECIMAL: lambda x: str(Decimal(str(x))),
            FieldType.BOOLEAN: lambda x: "1" if x else "0",
            FieldType.DATE: lambda x: x.isoformat() if isinstance(x, date) else str(x),
            FieldType.DATETIME: lambda x: x.isoformat() if isinstance(x, datetime) else str(x),
            FieldType.JSON: lambda x: json.dumps(x, default=str),
            FieldType.BINARY: lambda x: x.hex() if isinstance(x, bytes) else str(x),
        }
        self._type_deserializers: Dict[FieldType, callable] = {
            FieldType.STRING: str,
            FieldType.INTEGER: int,
            FieldType.FLOAT: float,
            FieldType.DECIMAL: Decimal,
            FieldType.BOOLEAN: lambda x: x == "1",
            FieldType.DATE: lambda x: datetime.fromisoformat(x).date(),
            FieldType.DATETIME: datetime.fromisoformat,
            FieldType.JSON: json.loads,
            FieldType.BINARY: bytes.fromhex,
        }

    def _get_cipher(self, key_id: str) -> AESCipher:
        """Get or create a cipher for the given key ID."""
        if key_id not in self._ciphers:
            key = self._key_manager.get_key(key_id)
            if not key:
                key = self._key_manager.get_key(self._default_key_id)
            if not key:
                raise ValueError(f"No encryption key found for key_id: {key_id}")
            self._ciphers[key_id] = create_cipher(key=key.key_material, key_id=key_id)
        return self._ciphers[key_id]

    def encrypt_field(
        self,
        value: Any,
        config: EncryptedFieldConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Encrypt a field value."""
        if value is None:
            return ""

        serializer = self._type_serializers.get(config.field_type, str)
        serialized = serializer(value)

        associated_data = None
        if context:
            associated_data = json.dumps(context, sort_keys=True).encode("utf-8")

        cipher = self._get_cipher(config.key_id)

        if config.deterministic:
            return self._encrypt_deterministic(serialized, cipher, associated_data)

        return cipher.encrypt_string(serialized, associated_data)

    def decrypt_field(
        self,
        encrypted_value: str,
        config: EncryptedFieldConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Decrypt a field value."""
        if not encrypted_value:
            return None

        associated_data = None
        if context:
            associated_data = json.dumps(context, sort_keys=True).encode("utf-8")

        cipher = self._get_cipher(config.key_id)

        if config.deterministic:
            serialized = self._decrypt_deterministic(encrypted_value, cipher, associated_data)
        else:
            serialized = cipher.decrypt_string(encrypted_value, associated_data)

        deserializer = self._type_deserializers.get(config.field_type, str)
        return deserializer(serialized)

    def _encrypt_deterministic(
        self,
        value: str,
        cipher: AESCipher,
        associated_data: Optional[bytes] = None,
    ) -> str:
        """Encrypt with deterministic nonce for searchability."""
        nonce_source = value.encode("utf-8")
        if associated_data:
            nonce_source += associated_data
        nonce = hashlib.sha256(nonce_source).digest()[:12]

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = self._key_manager.get_key(cipher.key_id)
        aesgcm = AESGCM(key.key_material)
        ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), associated_data)

        import base64
        import struct
        version_byte = struct.pack("B", 1)
        return base64.b64encode(version_byte + nonce + ciphertext).decode("ascii")

    def _decrypt_deterministic(
        self,
        encrypted_value: str,
        cipher: AESCipher,
        associated_data: Optional[bytes] = None,
    ) -> str:
        """Decrypt deterministically encrypted value."""
        import base64
        data = base64.b64decode(encrypted_value)
        nonce = data[1:13]
        ciphertext = data[13:]

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = self._key_manager.get_key(cipher.key_id)
        aesgcm = AESGCM(key.key_material)
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)
        return plaintext.decode("utf-8")

    def create_search_token(
        self,
        value: Any,
        config: EncryptedFieldConfig,
    ) -> str:
        """Create a search token for a searchable encrypted field."""
        if not config.searchable:
            raise ValueError("Field is not configured for searching")

        if not config.deterministic:
            raise ValueError("Searchable fields must use deterministic encryption")

        return self.encrypt_field(value, config)

    def mask_field(
        self,
        value: Any,
        config: EncryptedFieldConfig,
    ) -> str:
        """Return a masked version of the field value."""
        if value is None:
            return ""

        str_value = str(value)

        if config.mask_format:
            return self._apply_mask_format(str_value, config.mask_format)

        length = len(str_value)
        if length <= 4:
            return "*" * length

        visible_chars = min(4, length // 4)
        return str_value[:visible_chars] + "*" * (length - visible_chars * 2) + str_value[-visible_chars:]

    def _apply_mask_format(self, value: str, mask_format: str) -> str:
        """Apply a specific mask format."""
        if mask_format == "email":
            if "@" in value:
                local, domain = value.rsplit("@", 1)
                masked_local = local[0] + "*" * (len(local) - 1) if local else ""
                return f"{masked_local}@{domain}"

        if mask_format == "phone":
            digits = "".join(c for c in value if c.isdigit())
            if len(digits) >= 4:
                return "*" * (len(digits) - 4) + digits[-4:]

        if mask_format == "card":
            digits = "".join(c for c in value if c.isdigit())
            if len(digits) >= 4:
                return "*" * (len(digits) - 4) + digits[-4:]

        if mask_format == "ssn":
            digits = "".join(c for c in value if c.isdigit())
            if len(digits) >= 4:
                return "***-**-" + digits[-4:]

        return "*" * len(value)


def encrypt_field(
    value: Any,
    field_name: str,
    field_type: FieldType = FieldType.STRING,
    key_id: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenience function to encrypt a field value."""
    encryptor = FieldEncryptor()
    config = EncryptedFieldConfig(
        field_name=field_name,
        field_type=field_type,
        key_id=key_id,
    )
    return encryptor.encrypt_field(value, config, context)


def decrypt_field(
    encrypted_value: str,
    field_name: str,
    field_type: FieldType = FieldType.STRING,
    key_id: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> Any:
    """Convenience function to decrypt a field value."""
    encryptor = FieldEncryptor()
    config = EncryptedFieldConfig(
        field_name=field_name,
        field_type=field_type,
        key_id=key_id,
    )
    return encryptor.decrypt_field(encrypted_value, config, context)


class EncryptedModel:
    """Mixin class for models with encrypted fields."""

    _encrypted_fields: Dict[str, EncryptedFieldConfig] = {}
    _field_encryptor: Optional[FieldEncryptor] = None

    @classmethod
    def get_encryptor(cls) -> FieldEncryptor:
        """Get or create the field encryptor."""
        if cls._field_encryptor is None:
            cls._field_encryptor = FieldEncryptor()
        return cls._field_encryptor

    @classmethod
    def register_encrypted_field(
        cls,
        field_name: str,
        field_type: FieldType = FieldType.STRING,
        key_id: str = "default",
        searchable: bool = False,
        deterministic: bool = False,
        mask_format: Optional[str] = None,
    ) -> None:
        """Register a field for encryption."""
        cls._encrypted_fields[field_name] = EncryptedFieldConfig(
            field_name=field_name,
            field_type=field_type,
            key_id=key_id,
            searchable=searchable,
            deterministic=deterministic or searchable,
            mask_format=mask_format,
        )

    def encrypt_fields(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Encrypt all registered fields on the instance."""
        encryptor = self.get_encryptor()
        for field_name, config in self._encrypted_fields.items():
            value = getattr(self, field_name, None)
            if value is not None and not isinstance(value, str):
                encrypted = encryptor.encrypt_field(value, config, context)
                setattr(self, f"_encrypted_{field_name}", encrypted)

    def decrypt_fields(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Decrypt all registered fields on the instance."""
        encryptor = self.get_encryptor()
        for field_name, config in self._encrypted_fields.items():
            encrypted_value = getattr(self, f"_encrypted_{field_name}", None)
            if encrypted_value:
                decrypted = encryptor.decrypt_field(encrypted_value, config, context)
                setattr(self, field_name, decrypted)

    def get_masked_field(self, field_name: str) -> str:
        """Get a masked version of an encrypted field."""
        if field_name not in self._encrypted_fields:
            raise ValueError(f"Field '{field_name}' is not configured for encryption")

        config = self._encrypted_fields[field_name]
        value = getattr(self, field_name, None)

        if value is None:
            return ""

        encryptor = self.get_encryptor()
        return encryptor.mask_field(value, config)


def encrypted_field(
    field_type: FieldType = FieldType.STRING,
    key_id: str = "default",
    searchable: bool = False,
    mask_format: Optional[str] = None,
):
    """Decorator to mark a field as encrypted."""
    def decorator(func):
        func._encrypted_field_config = EncryptedFieldConfig(
            field_name=func.__name__,
            field_type=field_type,
            key_id=key_id,
            searchable=searchable,
            deterministic=searchable,
            mask_format=mask_format,
        )
        return func
    return decorator
