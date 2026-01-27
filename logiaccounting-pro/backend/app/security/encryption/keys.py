"""
Key management for encryption in LogiAccounting Pro.
"""

import os
import json
import hashlib
import base64
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


KEY_SIZE = 32
NONCE_SIZE = 12


class KeyStatus(str, Enum):
    """Key lifecycle status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_ROTATION = "pending_rotation"
    ROTATED = "rotated"
    COMPROMISED = "compromised"
    DESTROYED = "destroyed"


class KeyType(str, Enum):
    """Types of encryption keys."""

    MASTER = "master"
    DATA = "data"
    FIELD = "field"
    TENANT = "tenant"
    SESSION = "session"
    BACKUP = "backup"


@dataclass
class EncryptionKey:
    """Encryption key with metadata."""

    key_id: str
    key_type: KeyType
    key_material: bytes
    status: KeyStatus = KeyStatus.ACTIVE
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    rotated_from: Optional[str] = None
    rotated_to: Optional[str] = None
    organization_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if key is currently active."""
        if self.status != KeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    @property
    def fingerprint(self) -> str:
        """Get key fingerprint for identification."""
        return hashlib.sha256(self.key_material).hexdigest()[:16]

    def to_dict(self, include_material: bool = False) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            "key_id": self.key_id,
            "key_type": self.key_type.value,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
            "rotated_from": self.rotated_from,
            "rotated_to": self.rotated_to,
            "organization_id": self.organization_id,
            "fingerprint": self.fingerprint,
            "metadata": self.metadata,
        }
        if include_material:
            data["key_material"] = base64.b64encode(self.key_material).decode("ascii")
        return data


class KeyManager:
    """Manages encryption keys throughout their lifecycle."""

    def __init__(
        self,
        master_key: Optional[bytes] = None,
        storage_path: Optional[str] = None,
    ):
        self._keys: Dict[str, EncryptionKey] = {}
        self._key_versions: Dict[str, List[str]] = {}
        self._master_key = master_key or self._derive_master_key()
        self._storage_path = storage_path
        self._master_cipher = AESGCM(self._master_key)
        self._initialize_default_keys()

    def _derive_master_key(self) -> bytes:
        """Derive master key from environment or generate new one."""
        env_key = os.environ.get("ENCRYPTION_MASTER_KEY")
        if env_key:
            if len(env_key) == 64:
                return bytes.fromhex(env_key)
            salt = os.environ.get("ENCRYPTION_SALT", "logiaccounting-pro").encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=KEY_SIZE,
                salt=salt,
                iterations=100000,
                backend=default_backend(),
            )
            return kdf.derive(env_key.encode("utf-8"))
        return os.urandom(KEY_SIZE)

    def _initialize_default_keys(self) -> None:
        """Initialize default encryption keys."""
        if "default" not in self._keys:
            self.generate_key("default", KeyType.DATA)
        if "field" not in self._keys:
            self.generate_key("field", KeyType.FIELD)

    def generate_key(
        self,
        key_id: str,
        key_type: KeyType = KeyType.DATA,
        expires_in_days: Optional[int] = None,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EncryptionKey:
        """Generate a new encryption key."""
        key_material = os.urandom(KEY_SIZE)
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        version = 1
        if key_id in self._key_versions:
            version = len(self._key_versions[key_id]) + 1

        versioned_id = f"{key_id}_v{version}"

        key = EncryptionKey(
            key_id=key_id,
            key_type=key_type,
            key_material=key_material,
            version=version,
            expires_at=expires_at,
            organization_id=organization_id,
            metadata=metadata or {},
        )

        self._keys[versioned_id] = key
        self._keys[key_id] = key

        if key_id not in self._key_versions:
            self._key_versions[key_id] = []
        self._key_versions[key_id].append(versioned_id)

        return key

    def get_key(self, key_id: str, version: Optional[int] = None) -> Optional[EncryptionKey]:
        """Get a key by ID and optional version."""
        if version:
            versioned_id = f"{key_id}_v{version}"
            return self._keys.get(versioned_id)
        return self._keys.get(key_id)

    def get_active_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get the active version of a key."""
        key = self._keys.get(key_id)
        if key and key.is_active:
            return key
        return None

    def list_keys(
        self,
        key_type: Optional[KeyType] = None,
        status: Optional[KeyStatus] = None,
        organization_id: Optional[str] = None,
    ) -> List[EncryptionKey]:
        """List keys with optional filtering."""
        seen_ids = set()
        keys = []

        for key_id, key in self._keys.items():
            if "_v" in key_id:
                continue
            if key.key_id in seen_ids:
                continue
            seen_ids.add(key.key_id)

            if key_type and key.key_type != key_type:
                continue
            if status and key.status != status:
                continue
            if organization_id and key.organization_id != organization_id:
                continue
            keys.append(key)

        return keys

    def rotate_key(
        self,
        key_id: str,
        expires_in_days: Optional[int] = None,
    ) -> EncryptionKey:
        """Rotate a key, creating a new version."""
        old_key = self.get_key(key_id)
        if not old_key:
            raise ValueError(f"Key not found: {key_id}")

        new_key = self.generate_key(
            key_id=key_id,
            key_type=old_key.key_type,
            expires_in_days=expires_in_days,
            organization_id=old_key.organization_id,
            metadata=old_key.metadata.copy(),
        )

        old_versioned_id = f"{key_id}_v{old_key.version}"
        old_key.status = KeyStatus.ROTATED
        old_key.rotated_at = datetime.utcnow()
        old_key.rotated_to = f"{key_id}_v{new_key.version}"

        new_key.rotated_from = old_versioned_id

        return new_key

    def mark_compromised(self, key_id: str) -> bool:
        """Mark a key as compromised."""
        key = self.get_key(key_id)
        if not key:
            return False

        key.status = KeyStatus.COMPROMISED

        for versioned_id in self._key_versions.get(key_id, []):
            if versioned_id in self._keys:
                self._keys[versioned_id].status = KeyStatus.COMPROMISED

        return True

    def destroy_key(self, key_id: str, version: Optional[int] = None) -> bool:
        """Securely destroy a key."""
        if version:
            versioned_id = f"{key_id}_v{version}"
            if versioned_id in self._keys:
                key = self._keys[versioned_id]
                key.key_material = os.urandom(KEY_SIZE)
                key.status = KeyStatus.DESTROYED
                return True
            return False

        key = self._keys.get(key_id)
        if not key:
            return False

        key.key_material = os.urandom(KEY_SIZE)
        key.status = KeyStatus.DESTROYED

        return True

    def encrypt_key_for_storage(self, key: EncryptionKey) -> bytes:
        """Encrypt a key for secure storage."""
        key_data = json.dumps({
            "key_id": key.key_id,
            "key_type": key.key_type.value,
            "key_material": base64.b64encode(key.key_material).decode("ascii"),
            "status": key.status.value,
            "version": key.version,
            "created_at": key.created_at.isoformat(),
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "organization_id": key.organization_id,
            "metadata": key.metadata,
        }).encode("utf-8")

        nonce = os.urandom(NONCE_SIZE)
        ciphertext = self._master_cipher.encrypt(nonce, key_data, None)
        return nonce + ciphertext

    def decrypt_key_from_storage(self, encrypted_data: bytes) -> EncryptionKey:
        """Decrypt a key from secure storage."""
        nonce = encrypted_data[:NONCE_SIZE]
        ciphertext = encrypted_data[NONCE_SIZE:]

        key_data = self._master_cipher.decrypt(nonce, ciphertext, None)
        data = json.loads(key_data.decode("utf-8"))

        return EncryptionKey(
            key_id=data["key_id"],
            key_type=KeyType(data["key_type"]),
            key_material=base64.b64decode(data["key_material"]),
            status=KeyStatus(data["status"]),
            version=data["version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            organization_id=data["organization_id"],
            metadata=data.get("metadata", {}),
        )

    def save_keys(self, path: Optional[str] = None) -> None:
        """Save all keys to encrypted storage."""
        storage_path = path or self._storage_path
        if not storage_path:
            return

        keys_data = []
        for key_id, key in self._keys.items():
            if "_v" not in key_id:
                continue
            encrypted = self.encrypt_key_for_storage(key)
            keys_data.append(base64.b64encode(encrypted).decode("ascii"))

        Path(storage_path).write_text(json.dumps({
            "version": 1,
            "keys": keys_data,
            "saved_at": datetime.utcnow().isoformat(),
        }))

    def load_keys(self, path: Optional[str] = None) -> int:
        """Load keys from encrypted storage."""
        storage_path = path or self._storage_path
        if not storage_path or not Path(storage_path).exists():
            return 0

        data = json.loads(Path(storage_path).read_text())
        loaded = 0

        for encrypted_b64 in data.get("keys", []):
            encrypted = base64.b64decode(encrypted_b64)
            key = self.decrypt_key_from_storage(encrypted)

            versioned_id = f"{key.key_id}_v{key.version}"
            self._keys[versioned_id] = key
            self._keys[key.key_id] = key

            if key.key_id not in self._key_versions:
                self._key_versions[key.key_id] = []
            if versioned_id not in self._key_versions[key.key_id]:
                self._key_versions[key.key_id].append(versioned_id)

            loaded += 1

        return loaded

    def get_key_audit_info(self, key_id: str) -> Dict[str, Any]:
        """Get audit information for a key."""
        key = self.get_key(key_id)
        if not key:
            return {}

        versions = self._key_versions.get(key_id, [])

        return {
            "key_id": key_id,
            "current_version": key.version,
            "total_versions": len(versions),
            "status": key.status.value,
            "created_at": key.created_at.isoformat(),
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "is_active": key.is_active,
            "fingerprint": key.fingerprint,
            "version_history": [
                {
                    "version": self._keys[v].version,
                    "status": self._keys[v].status.value,
                    "created_at": self._keys[v].created_at.isoformat(),
                }
                for v in versions if v in self._keys
            ],
        }


_key_manager: Optional[KeyManager] = None


def get_key_manager() -> KeyManager:
    """Get the global key manager instance."""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager


def set_key_manager(manager: KeyManager) -> None:
    """Set the global key manager instance."""
    global _key_manager
    _key_manager = manager


def generate_key(
    key_id: str,
    key_type: KeyType = KeyType.DATA,
    expires_in_days: Optional[int] = None,
) -> EncryptionKey:
    """Generate a new encryption key using the global manager."""
    return get_key_manager().generate_key(key_id, key_type, expires_in_days)


def rotate_key(key_id: str) -> EncryptionKey:
    """Rotate a key using the global manager."""
    return get_key_manager().rotate_key(key_id)
