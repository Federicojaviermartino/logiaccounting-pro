"""
Local File System Storage Provider - Phase 13
For development and testing
"""

from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import os
from app.utils.datetime_utils import utc_now
import shutil
import hashlib
import json
import logging
from pathlib import Path

from .base import StorageProvider, StorageObject

logger = logging.getLogger(__name__)


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider"""

    name = "local"

    def __init__(self):
        self.base_path = os.getenv('LOCAL_STORAGE_PATH', '/tmp/logiaccounting-documents')
        self.base_url = os.getenv('LOCAL_STORAGE_URL', '/api/v1/files')

        # Ensure base directory exists
        os.makedirs(self.base_path, exist_ok=True)

    def _get_full_path(self, bucket: str, key: str) -> str:
        """Get full filesystem path with path traversal protection."""
        full_path = os.path.normpath(os.path.join(self.base_path, bucket, key))
        base = os.path.normpath(self.base_path)
        if not full_path.startswith(base + os.sep) and full_path != base:
            raise ValueError("Invalid path: path traversal detected")
        return full_path

    def _ensure_directory(self, file_path: str):
        """Ensure parent directory exists"""
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

    def upload(
        self,
        file_data: BinaryIO,
        key: str,
        bucket: str = 'default',
        content_type: str = None,
        metadata: Dict[str, str] = None,
        acl: str = 'private'
    ) -> StorageObject:
        """Upload file to local storage"""
        full_path = self._get_full_path(bucket, key)
        self._ensure_directory(full_path)

        content = file_data.read()
        with open(full_path, 'wb') as f:
            f.write(content)

        file_hash = hashlib.md5(content).hexdigest()

        meta_path = full_path + '.meta'
        with open(meta_path, 'w') as f:
            json.dump({
                'content_type': content_type or self._guess_content_type(key),
                'metadata': metadata or {},
                'size': len(content),
                'etag': file_hash,
                'created_at': utc_now().isoformat(),
            }, f)

        return StorageObject(
            key=key,
            bucket=bucket,
            size=len(content),
            content_type=content_type or self._guess_content_type(key),
            etag=file_hash,
            last_modified=utc_now(),
            metadata=metadata,
            url=f"{self.base_url}/{bucket}/{key}",
        )

    def upload_bytes(
        self,
        content: bytes,
        key: str,
        bucket: str = 'default',
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> StorageObject:
        """Upload bytes to local storage"""
        full_path = self._get_full_path(bucket, key)
        self._ensure_directory(full_path)

        with open(full_path, 'wb') as f:
            f.write(content)

        file_hash = hashlib.md5(content).hexdigest()

        meta_path = full_path + '.meta'
        with open(meta_path, 'w') as f:
            json.dump({
                'content_type': content_type or self._guess_content_type(key),
                'metadata': metadata or {},
                'size': len(content),
                'etag': file_hash,
                'created_at': utc_now().isoformat(),
            }, f)

        return StorageObject(
            key=key,
            bucket=bucket,
            size=len(content),
            content_type=content_type or self._guess_content_type(key),
            etag=file_hash,
            last_modified=utc_now(),
            metadata=metadata,
            url=f"{self.base_url}/{bucket}/{key}",
        )

    def download(self, key: str, bucket: str = 'default') -> bytes:
        """Download file from local storage"""
        full_path = self._get_full_path(bucket, key)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {key}")

        with open(full_path, 'rb') as f:
            return f.read()

    def download_to_file(
        self,
        key: str,
        bucket: str = 'default',
        file_path: str = None
    ) -> str:
        """Download file to local path"""
        full_path = self._get_full_path(bucket, key)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {key}")

        shutil.copy2(full_path, file_path)
        return file_path

    def delete(self, key: str, bucket: str = 'default') -> bool:
        """Delete file from local storage"""
        full_path = self._get_full_path(bucket, key)
        meta_path = full_path + '.meta'

        try:
            if os.path.exists(full_path):
                os.remove(full_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
            return True
        except Exception as e:
            logger.error(f"Local delete error: {e}")
            return False

    def exists(self, key: str, bucket: str = 'default') -> bool:
        """Check if file exists"""
        full_path = self._get_full_path(bucket, key)
        return os.path.exists(full_path)

    def get_metadata(self, key: str, bucket: str = 'default') -> Optional[StorageObject]:
        """Get file metadata"""
        full_path = self._get_full_path(bucket, key)
        meta_path = full_path + '.meta'

        if not os.path.exists(full_path):
            return None

        stats = os.stat(full_path)
        metadata = {}
        content_type = self._guess_content_type(key)
        etag = None

        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                content_type = meta.get('content_type', content_type)
                metadata = meta.get('metadata', {})
                etag = meta.get('etag')

        return StorageObject(
            key=key,
            bucket=bucket,
            size=stats.st_size,
            content_type=content_type,
            etag=etag,
            last_modified=datetime.fromtimestamp(stats.st_mtime),
            metadata=metadata,
            url=f"{self.base_url}/{bucket}/{key}",
        )

    def get_signed_url(
        self,
        key: str,
        bucket: str = 'default',
        expires_in: int = 3600,
        method: str = 'GET'
    ) -> str:
        """Generate URL (not actually signed for local storage)"""
        return f"{self.base_url}/{bucket}/{key}"

    def copy(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str = 'default',
        dest_bucket: str = None
    ) -> StorageObject:
        """Copy file"""
        dest_bucket = dest_bucket or source_bucket

        source_path = self._get_full_path(source_bucket, source_key)
        dest_path = self._get_full_path(dest_bucket, dest_key)

        self._ensure_directory(dest_path)

        shutil.copy2(source_path, dest_path)

        source_meta = source_path + '.meta'
        dest_meta = dest_path + '.meta'
        if os.path.exists(source_meta):
            shutil.copy2(source_meta, dest_meta)

        return self.get_metadata(dest_key, dest_bucket)

    def list_objects(
        self,
        prefix: str,
        bucket: str = 'default',
        max_keys: int = 1000,
        continuation_token: str = None
    ) -> Dict[str, Any]:
        """List objects with prefix"""
        bucket_path = os.path.join(self.base_path, bucket)

        if not os.path.exists(bucket_path):
            return {'objects': []}

        objects = []

        for root, dirs, files in os.walk(bucket_path):
            for file in files:
                if file.endswith('.meta'):
                    continue

                full_path = os.path.join(root, file)
                key = os.path.relpath(full_path, bucket_path).replace('\\', '/')

                if prefix and not key.startswith(prefix):
                    continue

                stats = os.stat(full_path)

                objects.append(StorageObject(
                    key=key,
                    bucket=bucket,
                    size=stats.st_size,
                    content_type=self._guess_content_type(key),
                    last_modified=datetime.fromtimestamp(stats.st_mtime),
                ))

                if len(objects) >= max_keys:
                    break

        return {'objects': objects}
