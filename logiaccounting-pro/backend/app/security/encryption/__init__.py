"""
Encryption module for LogiAccounting Pro.
"""

from .aes import (
    AESCipher,
    PasswordBasedCipher,
    EncryptionMetadata,
    create_cipher,
    create_password_cipher,
    KEY_SIZE,
    NONCE_SIZE,
)

from .fields import (
    FieldType,
    EncryptedFieldConfig,
    FieldEncryptor,
    EncryptedModel,
    encrypt_field,
    decrypt_field,
    encrypted_field,
)

from .keys import (
    KeyStatus,
    KeyType,
    EncryptionKey,
    KeyManager,
    get_key_manager,
    set_key_manager,
    generate_key,
    rotate_key,
)

__all__ = [
    "AESCipher",
    "PasswordBasedCipher",
    "EncryptionMetadata",
    "create_cipher",
    "create_password_cipher",
    "KEY_SIZE",
    "NONCE_SIZE",
    "FieldType",
    "EncryptedFieldConfig",
    "FieldEncryptor",
    "EncryptedModel",
    "encrypt_field",
    "decrypt_field",
    "encrypted_field",
    "KeyStatus",
    "KeyType",
    "EncryptionKey",
    "KeyManager",
    "get_key_manager",
    "set_key_manager",
    "generate_key",
    "rotate_key",
]
