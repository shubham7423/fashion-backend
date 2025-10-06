"""
Unified image storage service that can use either local filesystem or Google Cloud Storage.

This service provides a consistent interface for storing and retrieving images,
abstracting away the underlying storage mechanism.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from PIL import Image

from app.core.config import settings
from app.core.gcs_service import get_gcs_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ImageStorageService:
    """Service for storing and retrieving images using either local storage or GCS."""
    
    def __init__(self):
        """
        Selects and configures the storage backend (Google Cloud Storage or local filesystem) for the service.
        
        If GCS is configured and available, initializes `self.gcs_service` and enables GCS storage; otherwise falls back to local filesystem storage. Sets `self.use_gcs` to reflect the chosen backend and logs the outcome.
        """
        self.use_gcs = settings.USE_GCS and bool(settings.GCS_BUCKET_NAME)
        
        if self.use_gcs:
            self.gcs_service = get_gcs_service()
            if self.gcs_service.is_available:
                logger.info("Using Google Cloud Storage for image storage")
            else:
                logger.warning("GCS configured but not available, falling back to local storage")
                self.use_gcs = False
        
        if not self.use_gcs:
            logger.info("Using local filesystem for image storage")
    
    def save_processed_image(
        self, 
        image: Image.Image, 
        unique_filename: str, 
        user_id: str = None
    ) -> Optional[str]:
        """
        Save a processed PIL Image to the configured storage backend (GCS or local filesystem).
        
        Parameters:
            image (PIL.Image.Image): The processed image to save.
            unique_filename (str): Filename to use for the stored image (without storage path).
            user_id (str, optional): Identifier used to namespace the image when per-user subdirectories are enabled.
        
        Returns:
            saved_path (Optional[str]): The storage path or URL of the saved image on success, `None` on failure or when saving is disabled.
        """
        if not settings.SAVE_IMAGES or not settings.SAVE_PROCESSED:
            logger.info(f"[user={user_id}] Skipping image save (SAVE_IMAGES or SAVE_PROCESSED is False)")
            return None
        
        if self.use_gcs:
            return self._save_to_gcs(image, unique_filename, user_id)
        else:
            return self._save_to_local(image, unique_filename, user_id)
    
    def _save_to_gcs(
        self, 
        image: Image.Image, 
        unique_filename: str, 
        user_id: str = None
    ) -> Optional[str]:
        """
        Save a processed image to Google Cloud Storage and return its GCS URL.
        
        Saves the provided PIL Image as a JPEG into the configured GCS bucket, optionally placing it under a per-user subdirectory when user ID subdirectories are enabled. The uploaded object includes metadata with the uploader identifier, the original filename, the processed filename, and the user ID.
        
        Parameters:
            image (Image.Image): The PIL image to upload (will be encoded as JPEG).
            unique_filename (str): Original or unique filename used to derive the stored processed filename.
            user_id (str, optional): Identifier for the uploading user; used for metadata and optional namespacing.
        
        Returns:
            Optional[str]: The gs:// URL of the uploaded object if successful, `None` on failure.
        """
        try:
            # Create GCS blob path
            file_path = Path(unique_filename)
            processed_filename = f"{file_path.stem}_processed.jpg"
            
            # Organize by user if specified
            if user_id and settings.CREATE_USER_SUBDIRS:
                from app.core.user_id_utils import normalize_user_id
                normalized_user_id = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
                blob_name = f"{normalized_user_id}/processed/{processed_filename}"
            else:
                blob_name = f"processed/{processed_filename}"
            
            # Create metadata
            metadata = {
                "user_id": user_id or "anonymous",
                "original_filename": unique_filename,
                "processed_filename": processed_filename,
                "uploaded_by": "fashion-backend-api"
            }
            
            # Upload to GCS
            gcs_url = self.gcs_service.upload_image(
                image=image,
                blob_name=blob_name,
                format="JPEG",
                quality=settings.JPEG_QUALITY,
                metadata=metadata
            )
            
            if gcs_url:
                logger.info(f"[user={user_id}] Processed image saved to GCS: {blob_name}")
                return gcs_url
            else:
                logger.error(f"[user={user_id}] Failed to save image to GCS")
                return None
                
        except Exception as e:
            logger.error(f"[user={user_id}] Error saving image to GCS: {e}")
            return None
    
    def _save_to_local(
        self, 
        image: Image.Image, 
        unique_filename: str, 
        user_id: str = None
    ) -> Optional[str]:
        """
        Save a processed PIL image to the local images directory for a user.
        
        The image is written as a JPEG file named "<original_stem>_processed.jpg" inside the user's processed images directory. If saved successfully, returns the filesystem path to the saved file as a string.
        
        Parameters:
            image (PIL.Image.Image): The image to save.
            unique_filename (str): Original filename used to derive the processed filename (stem is preserved).
            user_id (str, optional): Identifier for the user; determines the user-specific images directory when provided.
        
        Returns:
            saved_path (str or None): Filesystem path of the saved JPEG on success, `None` on failure.
        """
        try:
            # Use the existing local storage logic
            from app.services.attribution_service import ClothingAttributionService
            
            images_dir = ClothingAttributionService.ensure_images_directory(user_id)
            processed_dir = images_dir / "processed"
            file_path = Path(unique_filename)
            processed_filename = f"{file_path.stem}_processed.jpg"
            file_path = processed_dir / processed_filename
            
            image.save(
                file_path, 
                format="JPEG", 
                quality=settings.JPEG_QUALITY, 
                optimize=True
            )
            
            logger.info(f"[user={user_id}] Processed image saved locally: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"[user={user_id}] Error saving image locally: {e}")
            return None
    
    def get_image(self, image_path: str) -> Optional[bytes]:
        """
        Retrieve image bytes for the given storage path or URL.
        
        Parameters:
            image_path (str): Local filesystem path or a GCS URL beginning with "gs://".
        
        Returns:
            bytes or None: `bytes` of the image if found, `None` otherwise.
        """
        if image_path.startswith("gs://"):
            return self._get_from_gcs(image_path)
        else:
            return self._get_from_local(image_path)
    
    def _get_from_gcs(self, gcs_url: str) -> Optional[bytes]:
        """
        Retrieve image bytes from Google Cloud Storage for the given GCS URL.
        
        Parameters:
            gcs_url (str): GCS path in the form "gs://{bucket}/path/to/blob". The bucket portion must match the configured GCS bucket.
        
        Returns:
            bytes | None: Image bytes if the blob is found and downloaded, `None` on error or if retrieval fails.
        """
        try:
            # Extract blob name from GCS URL
            # gs://bucket-name/path/to/file.jpg -> path/to/file.jpg
            blob_name = gcs_url.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
            return self.gcs_service.download_image(blob_name)
        except Exception as e:
            logger.error(f"Error retrieving image from GCS: {e}")
            return None
    
    def _get_from_local(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve the raw bytes of an image file from the local filesystem.
        
        Returns:
            image_bytes (bytes): Contents of the file as bytes if the file exists and is readable, `None` otherwise.
        """
        try:
            path = Path(file_path)
            if path.exists():
                return path.read_bytes()
            else:
                logger.warning(f"Local image file not found: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Error reading local image file: {e}")
            return None
    
    def delete_image(self, image_path: str) -> bool:
        """
        Remove an image identified by a local filesystem path or a GCS URL from storage.
        
        Parameters:
            image_path (str): Path to the image; either a local file path or a GCS URL starting with "gs://".
        
        Returns:
            bool: `True` if the image was deleted, `False` otherwise.
        """
        if image_path.startswith("gs://"):
            return self._delete_from_gcs(image_path)
        else:
            return self._delete_from_local(image_path)
    
    def _delete_from_gcs(self, gcs_url: str) -> bool:
        """
        Delete the object in Google Cloud Storage identified by the given GCS URL.
        
        Parameters:
            gcs_url (str): GCS object identifier, typically a full URL starting with "gs://{bucket}/" or a blob path that includes the bucket prefix.
        
        Returns:
            bool: `True` if the image was deleted, `False` otherwise.
        """
        try:
            blob_name = gcs_url.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
            return self.gcs_service.delete_image(blob_name)
        except Exception as e:
            logger.error(f"Error deleting image from GCS: {e}")
            return False
    
    def _delete_from_local(self, file_path: str) -> bool:
        """
        Deletes the file at file_path from the local filesystem.
        
        Returns:
            bool: `True` if the file was deleted, `False` if the file did not exist or if an error occurred during deletion.
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted local image: {file_path}")
                return True
            else:
                logger.warning(f"Local image file not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting local image file: {e}")
            return False
    
    def list_user_images(self, user_id: str) -> list:
        """
        Return all image paths or URLs associated with the given user.
        
        Parameters:
        	user_id (str): Identifier of the user whose images to list.
        
        Returns:
        	list: A list of image paths (local filesystem paths) or GCS URLs for the user's images.
        """
        if self.use_gcs:
            return self._list_from_gcs(user_id)
        else:
            return self._list_from_local(user_id)
    
    def _list_from_gcs(self, user_id: str) -> list:
        """
        List image objects in Google Cloud Storage for a given user and return their GCS URLs.
        
        If user subdirectories are enabled, the user_id is normalized and used as a prefix (normalized_user_id/processed/); otherwise the prefix is "processed/". Converts found blob names to full `gs://{bucket}/{blob}` URLs. Returns an empty list if an error occurs or no images are found.
        
        Parameters:
            user_id (str): Identifier of the user whose images should be listed; used for prefixing and normalization when configured.
        
        Returns:
            list: A list of GCS URLs (strings) for the user's processed images, or an empty list on failure.
        """
        try:
            if settings.CREATE_USER_SUBDIRS:
                from app.core.user_id_utils import normalize_user_id
                normalized_user_id = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
                prefix = f"{normalized_user_id}/processed/"
            else:
                prefix = "processed/"
            
            blob_names = self.gcs_service.list_images(prefix=prefix)
            # Convert to full GCS URLs
            return [f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}" for blob_name in blob_names]
        except Exception as e:
            logger.error(f"Error listing images from GCS for user {user_id}: {e}")
            return []
    
    def _list_from_local(self, user_id: str) -> list:
        """
        List image file paths for a user's processed local images.
        
        Parameters:
            user_id (str): Identifier of the user whose images directory will be searched.
        
        Returns:
            list: File system paths (strings) to JPEG files found in the user's "processed" directory; returns an empty list if no images are found or an error occurs.
        """
        try:
            from app.services.attribution_service import ClothingAttributionService
            
            images_dir = ClothingAttributionService.ensure_images_directory(user_id)
            processed_dir = images_dir / "processed"
            
            if processed_dir.exists():
                image_files = list(processed_dir.glob("*.jpg"))
                return [str(f) for f in image_files]
            else:
                return []
        except Exception as e:
            logger.error(f"Error listing local images for user {user_id}: {e}")
            return []
    
    def get_download_url(self, image_path: str, expiration_minutes: int = 60) -> Optional[str]:
        """
        Return a downloadable URL or path for the specified image.
        
        Parameters:
            image_path (str): A GCS URL (`gs://bucket/blob`), a GCS blob name, or a local file path.
            expiration_minutes (int): Expiration time in minutes for generated signed URLs (GCS only).
        
        Returns:
            str: A signed GCS URL when using GCS, a local-serveable path string for local storage (prefixed with `/images/` if relative), or `None` if `image_path` is empty.
        """
        if not image_path:
            return None
            
        # For GCS storage
        if self.use_gcs:
            if image_path.startswith("gs://"):
                # Extract blob name from GCS URL
                blob_name = image_path.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
            else:
                # Assume it's a blob name
                blob_name = image_path
            
            # Generate signed URL for secure access
            return self.gcs_service.generate_signed_url(blob_name, expiration_minutes)
        
        # For local storage, we can't provide a direct URL without a file server
        # This would typically require setting up a static file server
        # For now, return the local path (application will need to handle serving)
        else:
            return f"/images/{image_path}" if not image_path.startswith("/") else image_path

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Return a dictionary describing the active image storage configuration.
        
        The returned dictionary includes:
        - storage_type: "gcs" or "local".
        - save_images: whether images are saved (from settings).
        - save_processed: whether processed images are saved (from settings).
        If using GCS:
        - gcs_bucket: the configured GCS bucket name.
        - gcs_available: whether the GCS service is currently available.
        If using local storage:
        - images_directory: configured local images directory path.
        - user_data_directory: configured user data directory path.
        - create_user_subdirs: whether user subdirectories are created.
        
        Returns:
            info (Dict[str, Any]): Mapping of storage configuration keys to their current values.
        """
        info = {
            "storage_type": "gcs" if self.use_gcs else "local",
            "save_images": settings.SAVE_IMAGES,
            "save_processed": settings.SAVE_PROCESSED,
        }
        
        if self.use_gcs:
            info.update({
                "gcs_bucket": settings.GCS_BUCKET_NAME,
                "gcs_available": self.gcs_service.is_available if self.use_gcs else False,
            })
        else:
            info.update({
                "images_directory": settings.IMAGES_DIRECTORY,
                "user_data_directory": settings.USER_DATA_DIRECTORY,
                "create_user_subdirs": settings.CREATE_USER_SUBDIRS,
            })
        
        return info


# Global image storage service instance
_image_storage_service = None

def get_image_storage_service() -> ImageStorageService:
    """
    Return the global singleton ImageStorageService instance.
    
    Returns:
        ImageStorageService: The module-level singleton instance created on first access if not already initialized.
    """
    global _image_storage_service
    
    if _image_storage_service is None:
        _image_storage_service = ImageStorageService()
    
    return _image_storage_service