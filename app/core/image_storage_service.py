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
        """Initialize the image storage service."""
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
        Save a processed image using the configured storage backend.
        
        Args:
            image: PIL Image object to save
            unique_filename: Unique filename for the image
            user_id: User ID for organizing images
            
        Returns:
            Storage path/URL if successful, None otherwise
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
        """Save image to Google Cloud Storage."""
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
        """Save image to local filesystem."""
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
        Retrieve image bytes from storage.
        
        Args:
            image_path: Local path or GCS URL
            
        Returns:
            Image bytes if found, None otherwise
        """
        if image_path.startswith("gs://"):
            return self._get_from_gcs(image_path)
        else:
            return self._get_from_local(image_path)
    
    def _get_from_gcs(self, gcs_url: str) -> Optional[bytes]:
        """Get image from GCS."""
        try:
            # Extract blob name from GCS URL
            # gs://bucket-name/path/to/file.jpg -> path/to/file.jpg
            blob_name = gcs_url.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
            return self.gcs_service.download_image(blob_name)
        except Exception as e:
            logger.error(f"Error retrieving image from GCS: {e}")
            return None
    
    def _get_from_local(self, file_path: str) -> Optional[bytes]:
        """Get image from local filesystem."""
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
        Delete an image from storage.
        
        Args:
            image_path: Local path or GCS URL
            
        Returns:
            True if successful, False otherwise
        """
        if image_path.startswith("gs://"):
            return self._delete_from_gcs(image_path)
        else:
            return self._delete_from_local(image_path)
    
    def _delete_from_gcs(self, gcs_url: str) -> bool:
        """Delete image from GCS."""
        try:
            blob_name = gcs_url.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
            return self.gcs_service.delete_image(blob_name)
        except Exception as e:
            logger.error(f"Error deleting image from GCS: {e}")
            return False
    
    def _delete_from_local(self, file_path: str) -> bool:
        """Delete image from local filesystem."""
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
        List all images for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of image paths/URLs
        """
        if self.use_gcs:
            return self._list_from_gcs(user_id)
        else:
            return self._list_from_local(user_id)
    
    def _list_from_gcs(self, user_id: str) -> list:
        """List user images from GCS."""
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
        """List user images from local filesystem."""
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
        Get a download URL for an image.
        
        Args:
            image_path: Local path or GCS URL/blob name
            expiration_minutes: URL expiration time in minutes (for GCS signed URLs)
            
        Returns:
            Download URL if available, None otherwise
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
        """Get information about the current storage configuration."""
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
    """Get the global image storage service instance."""
    global _image_storage_service
    
    if _image_storage_service is None:
        _image_storage_service = ImageStorageService()
    
    return _image_storage_service
