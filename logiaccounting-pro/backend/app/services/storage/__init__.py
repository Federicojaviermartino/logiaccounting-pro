"""
Storage Service Module - Phase 13
Cloud storage abstraction layer supporting S3, Azure, GCS, and Local storage
"""

from .base import StorageProvider, StorageConfig, StorageObject
from .local_provider import LocalStorageProvider
from .s3_provider import S3StorageProvider
import os

__all__ = [
    'StorageProvider',
    'StorageConfig',
    'StorageObject',
    'LocalStorageProvider',
    'S3StorageProvider',
    'get_storage_provider',
]


def get_storage_provider(provider_name: str = None) -> StorageProvider:
    """Factory function to get storage provider"""
    provider_name = provider_name or os.getenv('STORAGE_PROVIDER', 'local')

    providers = {
        's3': S3StorageProvider,
        'local': LocalStorageProvider,
    }

    provider_class = providers.get(provider_name.lower())

    if not provider_class:
        raise ValueError(f"Unknown storage provider: {provider_name}")

    return provider_class()
