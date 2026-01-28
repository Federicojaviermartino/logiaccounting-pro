"""
Base Storage Provider - Phase 13
Abstract base class for storage implementations
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO, List
from dataclasses import dataclass
from datetime import datetime
import mimetypes
from app.utils.datetime_utils import utc_now
import os


@dataclass
class StorageConfig:
    """Storage configuration"""
    provider: str
    bucket: str
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    connection_string: Optional[str] = None
    account_name: Optional[str] = None
    project_id: Optional[str] = None
    credentials_path: Optional[str] = None


@dataclass
class StorageObject:
    """Represents a stored object"""
    key: str
    bucket: str
    size: int
    content_type: str
    etag: Optional[str] = None
    last_modified: Optional[datetime] = None
    metadata: Optional[Dict[str, str]] = None
    url: Optional[str] = None


class StorageProvider(ABC):
    """Abstract base class for storage providers"""

    name: str = "base"

    @abstractmethod
    def upload(
        self,
        file_data: BinaryIO,
        key: str,
        bucket: str,
        content_type: str = None,
        metadata: Dict[str, str] = None,
        acl: str = 'private'
    ) -> StorageObject:
        """Upload file to storage"""
        pass

    @abstractmethod
    def upload_bytes(
        self,
        content: bytes,
        key: str,
        bucket: str,
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> StorageObject:
        """Upload bytes to storage"""
        pass

    @abstractmethod
    def download(
        self,
        key: str,
        bucket: str
    ) -> bytes:
        """Download file from storage"""
        pass

    @abstractmethod
    def download_to_file(
        self,
        key: str,
        bucket: str,
        file_path: str
    ) -> str:
        """Download file to local path"""
        pass

    @abstractmethod
    def delete(
        self,
        key: str,
        bucket: str
    ) -> bool:
        """Delete file from storage"""
        pass

    @abstractmethod
    def exists(
        self,
        key: str,
        bucket: str
    ) -> bool:
        """Check if file exists"""
        pass

    @abstractmethod
    def get_metadata(
        self,
        key: str,
        bucket: str
    ) -> Optional[StorageObject]:
        """Get file metadata"""
        pass

    @abstractmethod
    def get_signed_url(
        self,
        key: str,
        bucket: str,
        expires_in: int = 3600,
        method: str = 'GET'
    ) -> str:
        """Generate signed URL for temporary access"""
        pass

    @abstractmethod
    def copy(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str,
        dest_bucket: str = None
    ) -> StorageObject:
        """Copy file within storage"""
        pass

    @abstractmethod
    def list_objects(
        self,
        prefix: str,
        bucket: str,
        max_keys: int = 1000,
        continuation_token: str = None
    ) -> Dict[str, Any]:
        """List objects with prefix"""
        pass

    def generate_key(
        self,
        organization_id: str,
        document_id: str,
        filename: str,
        version: int = None
    ) -> str:
        """Generate storage key with organization namespace"""
        safe_filename = self._safe_filename(filename)
        date_path = utc_now().strftime('%Y/%m')

        if version:
            return f"{organization_id}/documents/{date_path}/{document_id}/v{version}/{safe_filename}"
        else:
            return f"{organization_id}/documents/{date_path}/{document_id}/{safe_filename}"

    def _safe_filename(self, filename: str) -> str:
        """Generate safe filename"""
        import re
        safe = re.sub(r'[/\\:\x00]', '_', filename)
        if len(safe) > 200:
            name, ext = os.path.splitext(safe)
            safe = name[:200-len(ext)] + ext
        return safe

    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
