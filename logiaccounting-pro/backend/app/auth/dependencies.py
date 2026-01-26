"""
Authentication dependencies for FastAPI routes.
Re-exports auth utilities for cleaner imports.
"""

from app.utils.auth import (
    get_current_user,
    require_roles,
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
)

__all__ = [
    'get_current_user',
    'require_roles',
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'decode_token',
]
