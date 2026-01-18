"""
API Key Management Service
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class APIKeyService:
    """Manages API keys for external integrations"""

    _instance = None
    _keys: Dict[str, dict] = {}
    _counter = 0

    PERMISSIONS = {
        "materials": ["read", "write"],
        "transactions": ["read", "write"],
        "payments": ["read", "write"],
        "projects": ["read", "write"],
        "reports": ["read"]
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._keys = {}
            cls._counter = 0
        return cls._instance

    def generate_key(
        self,
        name: str,
        permissions: Dict[str, List[str]],
        expires_days: Optional[int] = 365,
        created_by: str = None
    ) -> dict:
        """Generate a new API key"""
        self._counter += 1
        key_id = f"KEY-{self._counter:04d}"

        raw_key = f"lap_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        expires_at = None
        if expires_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()

        key_data = {
            "id": key_id,
            "name": name,
            "key_hash": key_hash,
            "key_prefix": raw_key[:12],
            "permissions": permissions,
            "expires_at": expires_at,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "usage_count": 0,
            "active": True
        }

        self._keys[key_id] = key_data

        return {
            **{k: v for k, v in key_data.items() if k != "key_hash"},
            "key": raw_key
        }

    def validate_key(self, raw_key: str) -> Optional[dict]:
        """Validate an API key and return its data"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        for key_data in self._keys.values():
            if key_data["key_hash"] == key_hash:
                if not key_data["active"]:
                    return None

                if key_data["expires_at"]:
                    if datetime.fromisoformat(key_data["expires_at"]) < datetime.utcnow():
                        return None

                key_data["last_used"] = datetime.utcnow().isoformat()
                key_data["usage_count"] += 1

                return key_data

        return None

    def check_permission(self, key_data: dict, entity: str, action: str) -> bool:
        """Check if key has permission for action"""
        permissions = key_data.get("permissions", {})
        entity_perms = permissions.get(entity, [])
        return action in entity_perms

    def list_keys(self, user_id: Optional[str] = None) -> List[dict]:
        """List all API keys"""
        keys = list(self._keys.values())

        if user_id:
            keys = [k for k in keys if k["created_by"] == user_id]

        return [
            {k: v for k, v in key.items() if k != "key_hash"}
            for key in sorted(keys, key=lambda x: x["created_at"], reverse=True)
        ]

    def get_key(self, key_id: str) -> Optional[dict]:
        """Get API key by ID"""
        key = self._keys.get(key_id)
        if key:
            return {k: v for k, v in key.items() if k != "key_hash"}
        return None

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id in self._keys:
            self._keys[key_id]["active"] = False
            return True
        return False

    def delete_key(self, key_id: str) -> bool:
        """Delete an API key"""
        if key_id in self._keys:
            del self._keys[key_id]
            return True
        return False

    def update_permissions(self, key_id: str, permissions: Dict[str, List[str]]) -> Optional[dict]:
        """Update key permissions"""
        if key_id not in self._keys:
            return None

        self._keys[key_id]["permissions"] = permissions
        return self.get_key(key_id)


api_key_service = APIKeyService()
