"""
Unified data service that can use either local JSON files or Firebase Firestore.

This service provides a consistent interface for storing and retrieving user data,
with the ability to switch between local file storage and Firebase storage.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.core.firebase_utils import get_firebase_service
from app.core.user_id_utils import normalize_user_id
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UnifiedDataService:
    """Service that can use either local JSON or Firebase for data storage."""
    
    def __init__(self):
        """Initialize the service."""
        self.firebase_service = get_firebase_service()
        self.use_firebase = settings.USE_FIREBASE and self.firebase_service.is_available
        
        if self.use_firebase:
            logger.info("Using Firebase for data storage")
        else:
            logger.info("Using local JSON files for data storage")
    
    def get_user_json_file_path(self, user_id: str) -> Path:
        """Get the path to user's JSON file (for local storage)."""
        normalized_user_id = normalize_user_id(user_id)
        
        if settings.CREATE_USER_SUBDIRS:
            user_dir = Path(settings.USER_DATA_DIRECTORY) / normalized_user_id
            json_path = user_dir / settings.ATTRIBUTES_JSON_FILE
        else:
            json_path = Path(f"{normalized_user_id}_{settings.ATTRIBUTES_JSON_FILE}")
            
        return json_path
    
    def load_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Load user data from either Firebase or local JSON file.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dict containing user data if found, None otherwise
        """
        if self.use_firebase:
            return self._load_from_firebase(user_id)
        else:
            return self._load_from_json(user_id)
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Save user data to either Firebase or local JSON file.
        
        Args:
            user_id: Unique identifier for the user
            data: Dictionary containing user data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.use_firebase:
            return self._save_to_firebase(user_id, data)
        else:
            return self._save_to_json(user_id, data)
    
    def update_user_image(self, user_id: str, image_hash: str, image_data: Dict[str, Any]) -> bool:
        """
        Update or add image data for a user.
        
        Args:
            user_id: Unique identifier for the user
            image_hash: Unique hash for the image
            image_data: Dictionary containing image attributes and metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.use_firebase:
            return self.firebase_service.update_user_images(user_id, image_hash, image_data)
        else:
            # For local storage, load existing data, update, and save
            user_data = self.load_user_data(user_id) or {"images": {}}
            
            if "images" not in user_data:
                user_data["images"] = {}
            
            user_data["images"][image_hash] = image_data
            return self.save_user_data(user_id, user_data)
    
    def _load_from_firebase(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user data from Firebase."""
        return self.firebase_service.get_user_data(user_id)
    
    def _load_from_json(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user data from local JSON file."""
        json_file_path = self.get_user_json_file_path(user_id)
        
        if not json_file_path.exists():
            return None
        
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading user data from {json_file_path}: {e}")
            return None
    
    def _save_to_firebase(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Save user data to Firebase."""
        return self.firebase_service.store_user_data(user_id, data)
    
    def _save_to_json(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Save user data to local JSON file."""
        json_file_path = self.get_user_json_file_path(user_id)
        
        try:
            # Create directory if it doesn't exist
            json_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except IOError as e:
            logger.error(f"Error saving user data to {json_file_path}: {e}")
            return False
    
    def migrate_to_firebase(self, user_id: str) -> bool:
        """
        Migrate user data from local JSON to Firebase.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.firebase_service.is_available:
            logger.warning("Firebase not available for migration")
            return False
        
        # Load data from local JSON
        local_data = self._load_from_json(user_id)
        if not local_data:
            logger.warning(f"No local data found for user: {user_id}")
            return False
        
        # Save to Firebase
        success = self._save_to_firebase(user_id, local_data)
        if success:
            logger.info(f"Migrated user {user_id} data to Firebase")
        return success
    
    def backup_from_firebase(self, user_id: str) -> bool:
        """
        Backup user data from Firebase to local JSON.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.firebase_service.is_available:
            logger.warning("Firebase not available for backup")
            return False
        
        # Load data from Firebase
        firebase_data = self._load_from_firebase(user_id)
        if not firebase_data:
            logger.warning(f"No Firebase data found for user: {user_id}")
            return False
        
        # Save to local JSON
        success = self._save_to_json(user_id, firebase_data)
        if success:
            logger.info(f"Backed up user {user_id} data from Firebase to local JSON")
        return success


# Global unified data service instance
unified_data_service = UnifiedDataService()


def get_data_service() -> UnifiedDataService:
    """Get the global unified data service instance."""
    return unified_data_service
