"""
Firebase utilities for storing and retrieving JSON data.

This module provides a simple interface for interacting with Firebase Firestore
to store and retrieve user clothing attributes and other JSON data.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

from app.core.config import settings


class FirebaseService:
    """Service for Firebase Firestore operations."""
    
    def __init__(self):
        """Initialize Firebase service."""
        self._db = None
        self._initialized = False
        
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available. Install with: pip install firebase-admin")
            return
            
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self._db = firestore.client()
                self._initialized = True
                logger.info("Firebase client already initialized.")
                return
            
            # Get service account key path from settings
            service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY
            
            if service_account_path and Path(service_account_path).exists():
                # Initialize with service account key file
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized with service account key")
            else:
                # Try to initialize with default credentials (for local development)
                try:
                    firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
                except Exception as e:
                    logger.warning(f"Firebase initialization failed: {e}")
                    logger.info("Set FIREBASE_SERVICE_ACCOUNT_KEY environment variable or use default credentials")
                    return
            
            self._db = firestore.client()
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Firebase initialization error: {e}")
            self._initialized = False
    
    @property
    def is_available(self) -> bool:
        """Check if Firebase is available and initialized."""
        return FIREBASE_AVAILABLE and self._initialized and self._db is not None
    
    def store_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Store user data in Firebase Firestore.
        
        Args:
            user_id: Unique identifier for the user
            data: Dictionary containing user data to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available:
            logger.warning("Firebase not available, cannot store data")
            return False
        
        try:
            # Normalize user_id for consistent storage
            normalized_user_id = user_id.lower().strip()
            
            # Store in 'users' collection with user_id as document ID
            doc_ref = self._db.collection('users').document(normalized_user_id)
            
            # Add timestamp for tracking
            from datetime import datetime
            data_with_timestamp = {
                **data,
                'last_updated': datetime.utcnow(),
                'user_id': normalized_user_id
            }
            
            doc_ref.set(data_with_timestamp, merge=True)
            # Only log at debug level for successful store
            logger.debug(f"Stored data for user: {normalized_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing user data: {e}")
            return False
    
    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user data from Firebase Firestore.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dict containing user data if found, None otherwise
        """
        if not self.is_available:
            logger.warning("Firebase not available, cannot retrieve data")
            return None
        
        try:
            # Normalize user_id for consistent retrieval
            normalized_user_id = user_id.lower().strip()
            
            # Get document from 'users' collection
            doc_ref = self._db.collection('users').document(normalized_user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                logger.debug(f"Retrieved data for user: {normalized_user_id}")
                return data
            else:
                logger.warning(f"No data found for user: {normalized_user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving user data: {e}")
            return None
    
    def update_user_images(self, user_id: str, image_hash: str, image_data: Dict[str, Any]) -> bool:
        """
        Update or add image data for a user.
        
        Args:
            user_id: Unique identifier for the user
            image_hash: Unique hash for the image
            image_data: Dictionary containing image attributes and metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available:
            logger.warning("Firebase not available, cannot update images")
            return False
        
        try:
            normalized_user_id = user_id.lower().strip()
            
            # Update the specific image in the user's images collection
            doc_ref = self._db.collection('users').document(normalized_user_id)
            
            # Use Firestore's nested field update syntax
            update_data = {
                f'images.{image_hash}': image_data,
                'last_updated': firestore.SERVER_TIMESTAMP
            }
            
            doc_ref.set(update_data, merge=True)
            logger.debug(f"Updated image {image_hash[:8]}... for user: {normalized_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user images: {e}")
            return False
    
    def delete_user_data(self, user_id: str) -> bool:
        """
        Delete user data from Firebase Firestore.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available:
            logger.warning("Firebase not available, cannot delete data")
            return False
        
        try:
            normalized_user_id = user_id.lower().strip()
            
            # Delete document from 'users' collection
            doc_ref = self._db.collection('users').document(normalized_user_id)
            doc_ref.delete()
            logger.debug(f"Deleted data for user: {normalized_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            return False
    
    def list_users(self, limit: int = 50) -> List[str]:
        """
        List all user IDs in the database.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of user IDs
        """
        if not self.is_available:
            logger.warning("Firebase not available, cannot list users")
            return []
        
        try:
            users_ref = self._db.collection('users').limit(limit)
            docs = users_ref.stream()
            user_ids = [doc.id for doc in docs]
            logger.info(f"Listing users (count={len(user_ids)})")
            return user_ids
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    def backup_to_json(self, user_id: str, file_path: str) -> bool:
        """
        Backup user data from Firebase to a local JSON file.
        
        Args:
            user_id: Unique identifier for the user
            file_path: Path where to save the JSON backup
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Backing up user {user_id} to {file_path}")
        data = self.get_user_data(user_id)
        if not data:
            logger.warning(f"No data to backup for user: {user_id}")
            return False
        
        try:
            # Convert Firestore timestamps to strings for JSON serialization
            def convert_timestamps(obj):
                if hasattr(obj, 'timestamp'):
                    return obj.timestamp()
                return obj
            
            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"Backup complete for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up user data: {e}")
            return False
    
    def restore_from_json(self, user_id: str, file_path: str) -> bool:
        """
        Restore user data from a local JSON file to Firebase.
        
        Args:
            user_id: Unique identifier for the user
            file_path: Path to the JSON file to restore
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Restoring user {user_id} from {file_path}")
        try:
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            result = self.store_user_data(user_id, data)
            if result:
                logger.info(f"Restore complete for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error restoring user data: {e}")
            return False


# Global Firebase service instance
firebase_service = FirebaseService()


def get_firebase_service() -> FirebaseService:
    """Get the global Firebase service instance."""
    return firebase_service