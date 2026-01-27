"""
AWS S3 Storage Provider - Phase 13
Production cloud storage with S3-compatible APIs
"""

from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import os
import logging
from io import BytesIO

from .base import StorageProvider, StorageObject

logger = logging.getLogger(__name__)


class S3StorageProvider(StorageProvider):
    """AWS S3 Storage Provider"""

    name = "s3"

    def __init__(self):
        self.client = None
        self.default_bucket = os.getenv('S3_BUCKET', 'logiaccounting-documents')
        self._init_client()

    def _init_client(self):
        """Create S3 client lazily"""
        try:
            import boto3
            from botocore.config import Config

            config = Config(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )

            endpoint_url = os.getenv('S3_ENDPOINT_URL')

            self.client = boto3.client(
                's3',
                region_name=os.getenv('S3_REGION', 'us-east-1'),
                endpoint_url=endpoint_url,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                config=config
            )
        except ImportError:
            logger.warning("boto3 not installed. S3 storage will not work.")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.client = None

    def _ensure_client(self):
        """Ensure S3 client is available"""
        if not self.client:
            raise RuntimeError("S3 client not available. Install boto3 and configure credentials.")

    def upload(
        self,
        file_data: BinaryIO,
        key: str,
        bucket: str = None,
        content_type: str = None,
        metadata: Dict[str, str] = None,
        acl: str = 'private'
    ) -> StorageObject:
        """Upload file to S3"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        extra_args = {
            'ContentType': content_type or self._guess_content_type(key),
        }

        if acl:
            extra_args['ACL'] = acl

        if metadata:
            extra_args['Metadata'] = metadata

        try:
            self.client.upload_fileobj(
                file_data,
                bucket,
                key,
                ExtraArgs=extra_args
            )

            response = self.client.head_object(Bucket=bucket, Key=key)

            return StorageObject(
                key=key,
                bucket=bucket,
                size=response['ContentLength'],
                content_type=response['ContentType'],
                etag=response.get('ETag', '').strip('"'),
                last_modified=response.get('LastModified'),
                metadata=response.get('Metadata', {}),
            )

        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            raise

    def upload_bytes(
        self,
        content: bytes,
        key: str,
        bucket: str = None,
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> StorageObject:
        """Upload bytes to S3"""
        return self.upload(
            file_data=BytesIO(content),
            key=key,
            bucket=bucket,
            content_type=content_type,
            metadata=metadata
        )

    def download(self, key: str, bucket: str = None) -> bytes:
        """Download file from S3"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"S3 download error: {e}")
            raise

    def download_to_file(
        self,
        key: str,
        bucket: str = None,
        file_path: str = None
    ) -> str:
        """Download file to local path"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        try:
            self.client.download_file(bucket, key, file_path)
            return file_path
        except Exception as e:
            logger.error(f"S3 download to file error: {e}")
            raise

    def delete(self, key: str, bucket: str = None) -> bool:
        """Delete file from S3"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            logger.error(f"S3 delete error: {e}")
            return False

    def exists(self, key: str, bucket: str = None) -> bool:
        """Check if file exists in S3"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') == '404':
                return False
            raise

    def get_metadata(self, key: str, bucket: str = None) -> Optional[StorageObject]:
        """Get file metadata from S3"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        try:
            response = self.client.head_object(Bucket=bucket, Key=key)

            return StorageObject(
                key=key,
                bucket=bucket,
                size=response['ContentLength'],
                content_type=response['ContentType'],
                etag=response.get('ETag', '').strip('"'),
                last_modified=response.get('LastModified'),
                metadata=response.get('Metadata', {}),
            )
        except Exception as e:
            if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') == '404':
                return None
            raise

    def get_signed_url(
        self,
        key: str,
        bucket: str = None,
        expires_in: int = 3600,
        method: str = 'GET'
    ) -> str:
        """Generate presigned URL"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        client_method = 'get_object' if method == 'GET' else 'put_object'

        try:
            url = self.client.generate_presigned_url(
                client_method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"S3 presigned URL error: {e}")
            raise

    def copy(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str = None,
        dest_bucket: str = None
    ) -> StorageObject:
        """Copy file within S3"""
        self._ensure_client()
        source_bucket = source_bucket or self.default_bucket
        dest_bucket = dest_bucket or source_bucket

        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}

            self.client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )

            return self.get_metadata(dest_key, dest_bucket)

        except Exception as e:
            logger.error(f"S3 copy error: {e}")
            raise

    def list_objects(
        self,
        prefix: str,
        bucket: str = None,
        max_keys: int = 1000,
        continuation_token: str = None
    ) -> Dict[str, Any]:
        """List objects with prefix"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        params = {
            'Bucket': bucket,
            'Prefix': prefix,
            'MaxKeys': max_keys,
        }

        if continuation_token:
            params['ContinuationToken'] = continuation_token

        try:
            response = self.client.list_objects_v2(**params)

            objects = []
            for obj in response.get('Contents', []):
                objects.append(StorageObject(
                    key=obj['Key'],
                    bucket=bucket,
                    size=obj['Size'],
                    content_type='',
                    etag=obj.get('ETag', '').strip('"'),
                    last_modified=obj.get('LastModified'),
                ))

            result = {'objects': objects}

            if response.get('IsTruncated'):
                result['continuation_token'] = response.get('NextContinuationToken')

            return result

        except Exception as e:
            logger.error(f"S3 list error: {e}")
            raise

    def create_multipart_upload(
        self,
        key: str,
        bucket: str = None,
        content_type: str = None
    ) -> str:
        """Create multipart upload for large files"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        response = self.client.create_multipart_upload(
            Bucket=bucket,
            Key=key,
            ContentType=content_type or 'application/octet-stream'
        )

        return response['UploadId']

    def upload_part(
        self,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes,
        bucket: str = None
    ) -> Dict[str, Any]:
        """Upload a part of multipart upload"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        response = self.client.upload_part(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            PartNumber=part_number,
            Body=data
        )

        return {
            'PartNumber': part_number,
            'ETag': response['ETag']
        }

    def complete_multipart_upload(
        self,
        key: str,
        upload_id: str,
        parts: list,
        bucket: str = None
    ) -> StorageObject:
        """Complete multipart upload"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        self.client.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )

        return self.get_metadata(key, bucket)

    def abort_multipart_upload(
        self,
        key: str,
        upload_id: str,
        bucket: str = None
    ):
        """Abort multipart upload"""
        self._ensure_client()
        bucket = bucket or self.default_bucket

        self.client.abort_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id
        )
