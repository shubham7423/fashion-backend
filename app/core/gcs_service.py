"""
Google Cloud Storage service for storing and retrieving image files.

This module provides a service for interacting with Google Cloud Storage
to store and retrieve processed images instead of storing them locally.
"""

import io
import os
from typing import Optional, Dict, Any
from pathlib import Path
from PIL import Image

from app.core.logging_config import get_logger

logger = get_logger(__name__)

try:
    from google.cloud import storage
    from google.api_core import exceptions as gcp_exceptions
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("Google Cloud Storage client not available. Install with: pip install google-cloud-storage")


class GCSService:
    """Service for Google Cloud Storage operations."""
    
    def __init__(self, bucket_name: str, service_account_key_path: str = None):
        """
        Create a GCSService configured for a specific bucket and optional service account key.
        
        Stores the provided configuration on the instance and, if Google Cloud Storage support is available, attempts to initialize the internal GCS client and bucket reference.
        
        Parameters:
            bucket_name (str): Name of the target GCS bucket to operate on.
            service_account_key_path (str, optional): Filesystem path to a service account JSON key to use for authentication; if omitted, default credentials will be used when available.
        """
        self.bucket_name = bucket_name
        self.service_account_key_path = service_account_key_path
        self._client = None
        self._bucket = None
        self._initialized = False
        
        if GCS_AVAILABLE:
            self._initialize_gcs()
    
    def _initialize_gcs(self):
        """
        Initialize the Google Cloud Storage client and obtain a bucket reference for this service.
        
        If a valid service account key path was provided and exists, that key is used; otherwise default credentials are attempted. On success the method sets self._client and self._bucket and marks self._initialized True after verifying bucket access. On failure it logs the error and ensures self._initialized is False.
        """
        try:
            # Initialize client with service account key if provided
            if self.service_account_key_path and os.path.exists(self.service_account_key_path):
                self._client = storage.Client.from_service_account_json(self.service_account_key_path)
                logger.info("GCS initialized with service account key")
            else:
                # Try to use default credentials (for Cloud Run, Compute Engine, etc.)
                self._client = storage.Client()
                logger.info("GCS initialized with default credentials")
            
            # Get bucket reference
            self._bucket = self._client.bucket(self.bucket_name)
            
            # Test bucket access
            if self._bucket.exists():
                self._initialized = True
                logger.info(f"GCS bucket '{self.bucket_name}' is accessible")
            else:
                logger.error(f"GCS bucket '{self.bucket_name}' does not exist or is not accessible")
                
        except Exception as e:
            logger.error(f"Failed to initialize GCS: {e}")
            self._initialized = False
    
    @property
    def is_available(self) -> bool:
        """
        Indicates whether Google Cloud Storage bucket access is ready for operations.
        
        Returns:
            `True` if the Google Cloud Storage client is available and the target bucket was successfully initialized, `False` otherwise.
        """
        return GCS_AVAILABLE and self._initialized
    
    def upload_image(
        self, 
        image: Image.Image, 
        blob_name: str, 
        format: str = "JPEG",
        quality: int = 85,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Upload a PIL Image to the configured Google Cloud Storage bucket and return its GCS path.
        
        Parameters:
            image (PIL.Image.Image): Image to upload.
            blob_name (str): Destination blob name within the bucket (may include path segments).
            format (str): Image file format to use (e.g., "JPEG", "PNG"). Defaults to "JPEG".
            quality (int): JPEG quality value from 1 to 100; ignored for non-JPEG formats. Defaults to 85.
            metadata (Optional[Dict[str, str]]): Optional metadata to attach to the blob.
        
        Returns:
            Optional[str]: The GCS URI (gs://bucket_name/blob_name) on success, or `None` on failure or when GCS is unavailable.
        """
        if not self.is_available:
            logger.warning("GCS not available, cannot upload image")
            return None
        
        try:
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            if format.upper() == "JPEG":
                image.save(img_buffer, format=format, quality=quality, optimize=True)
            else:
                image.save(img_buffer, format=format, optimize=True)
            
            img_buffer.seek(0)
            
            # Create blob and upload
            blob = self._bucket.blob(blob_name)
            
            # Set content type based on format
            content_type = f"image/{format.lower()}"
            blob.content_type = content_type
            
            # Add custom metadata if provided
            if metadata:
                blob.metadata = metadata
            
            # Upload the image
            blob.upload_from_file(img_buffer, content_type=content_type)
            
            # Get the public URL
            gcs_url = f"gs://{self.bucket_name}/{blob_name}"
            
            logger.info(f"Image uploaded to GCS: {gcs_url}")
            return gcs_url
            
        except Exception as e:
            logger.error(f"Error uploading image to GCS: {e}")
            return None
    
    def upload_image_bytes(
        self, 
        image_bytes: bytes, 
        blob_name: str, 
        content_type: str = "image/jpeg",
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Upload raw image bytes to the configured Google Cloud Storage bucket as a blob.
        
        If provided, `metadata` is attached to the created blob.
        
        Parameters:
            image_bytes (bytes): Raw image data to upload.
            blob_name (str): Destination path/name for the blob in the bucket.
            content_type (str): MIME type to set for the blob (e.g., "image/jpeg").
            metadata (Optional[Dict[str, str]]): Optional key/value metadata to attach to the blob.
        
        Returns:
            The GCS URL in the form `gs://{bucket}/{blob}` on success, `None` otherwise.
        """
        if not self.is_available:
            logger.warning("GCS not available, cannot upload image bytes")
            return None
        
        try:
            blob = self._bucket.blob(blob_name)
            blob.content_type = content_type
            
            if metadata:
                blob.metadata = metadata
            
            blob.upload_from_string(image_bytes, content_type=content_type)
            
            gcs_url = f"gs://{self.bucket_name}/{blob_name}"
            logger.info(f"Image bytes uploaded to GCS: {gcs_url}")
            return gcs_url
            
        except Exception as e:
            logger.error(f"Error uploading image bytes to GCS: {e}")
            return None
    
    def download_image(self, blob_name: str) -> Optional[bytes]:
        """
        Download image bytes for a blob stored in Google Cloud Storage.
        
        Parameters:
            blob_name (str): Name of the blob to retrieve.
        
        Returns:
            Optional[bytes]: The blob's bytes if found and downloadable, `None` otherwise.
        """
        if not self.is_available:
            logger.warning("GCS not available, cannot download image")
            return None
        
        try:
            blob = self._bucket.blob(blob_name)
            
            if not blob.exists():
                logger.warning(f"Blob does not exist: {blob_name}")
                return None
            
            image_bytes = blob.download_as_bytes()
            logger.info(f"Image downloaded from GCS: {blob_name}")
            return image_bytes
            
        except Exception as e:
            logger.error(f"Error downloading image from GCS: {e}")
            return None
    
    def delete_image(self, blob_name: str) -> bool:
        """
        Delete an object from the configured GCS bucket.
        
        Parameters:
            blob_name (str): Path or name of the blob within the bucket to delete.
        
        Returns:
            bool: `True` if the blob existed and was deleted, `False` otherwise (including when GCS is unavailable, the blob does not exist, or an error occurs).
        """
        if not self.is_available:
            logger.warning("GCS not available, cannot delete image")
            return False
        
        try:
            blob = self._bucket.blob(blob_name)
            
            if blob.exists():
                blob.delete()
                logger.info(f"Image deleted from GCS: {blob_name}")
                return True
            else:
                logger.warning(f"Blob does not exist for deletion: {blob_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image from GCS: {e}")
            return False
    
    def list_images(self, prefix: str = "") -> list:
        """
        List blob names in the configured GCS bucket, optionally filtered by a prefix.
        
        Parameters:
            prefix (str): Prefix to filter blob names; empty string returns all blobs.
        
        Returns:
            list[str]: Blob names in the bucket that match the prefix.
        """
        if not self.is_available:
            logger.warning("GCS not available, cannot list images")
            return []
        
        try:
            blobs = self._bucket.list_blobs(prefix=prefix)
            blob_names = [blob.name for blob in blobs]
            logger.info(f"Listed {len(blob_names)} images from GCS with prefix '{prefix}'")
            return blob_names
            
        except Exception as e:
            logger.error(f"Error listing images from GCS: {e}")
            return []
    
    def get_public_url(self, blob_name: str) -> Optional[str]:
        """
        Get the publicly accessible URL for the named blob in the bucket.
        
        Parameters:
            blob_name (str): Name of the blob.
        
        Returns:
            The public URL string for the blob if it exists, `None` otherwise.
        """
        if not self.is_available:
            return None
        
        try:
            blob = self._bucket.blob(blob_name)
            if blob.exists():
                return blob.public_url
            return None
        except Exception as e:
            logger.error(f"Error getting public URL for {blob_name}: {e}")
            return None
    
    def generate_signed_url(
        self, 
        blob_name: str, 
        expiration_minutes: int = 60,
        method: str = "GET"
    ) -> Optional[str]:
        """
        Generate a V4 signed URL for accessing a blob in the configured GCS bucket.
        
        Parameters:
            blob_name (str): Name of the blob object in the bucket.
            expiration_minutes (int): Time in minutes until the signed URL expires.
            method (str): HTTP method allowed for the signed URL (e.g., "GET", "PUT").
        
        Returns:
            signed_url (str): The generated signed URL, or `None` if the service is unavailable or generation fails.
        """
        if not self.is_available:
            return None
        
        try:
            from datetime import datetime, timedelta
            
            blob = self._bucket.blob(blob_name)
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            
            signed_url = blob.generate_signed_url(
                expiration=expiration,
                method=method,
                version="v4"
            )
            
            logger.info(f"Generated signed URL for {blob_name} (expires in {expiration_minutes} min)")
            return signed_url
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {blob_name}: {e}")
            return None


# Global GCS service instance
_gcs_service = None

def get_gcs_service() -> GCSService:
    """
    Return the module-level singleton GCSService configured from application settings.
    
    If no instance exists, this function constructs one using settings.GCS_BUCKET_NAME and
    settings.GCS_SERVICE_ACCOUNT_KEY. If GCS_BUCKET_NAME is not configured, a dummy
    GCSService (reporting not available) is created and a warning is logged.
    
    Returns:
        GCSService: The global GCSService singleton instance.
    """
    global _gcs_service
    
    if _gcs_service is None:
        from app.core.config import settings
        
        bucket_name = getattr(settings, 'GCS_BUCKET_NAME', None)
        service_account_key = getattr(settings, 'GCS_SERVICE_ACCOUNT_KEY', None)
        
        if bucket_name:
            _gcs_service = GCSService(
                bucket_name=bucket_name,
                service_account_key_path=service_account_key
            )
        else:
            logger.warning("GCS_BUCKET_NAME not configured")
            # Create a dummy service that will always return is_available=False
            _gcs_service = GCSService("")
    
    return _gcs_service