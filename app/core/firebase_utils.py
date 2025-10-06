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
        """
        Set up the Firebase Admin SDK and obtain a Firestore client for this service.
        
        Initializes Firebase using the service account key path from settings.FIREBASE_SERVICE_ACCOUNT_KEY when that file exists; otherwise attempts to initialize with default credentials. If Firebase is already initialized, reuses the existing app. On successful initialization assigns the Firestore client to self._db and sets self._initialized to True. On failure leaves self._initialized False.
        """
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
        """
        Check whether Firebase is ready for use.
        
        Returns:
            `true` if the Firebase Admin SDK is present, initialization has completed, and a Firestore client is available; `false` otherwise.
        """
        return FIREBASE_AVAILABLE and self._initialized and self._db is not None
    
    def store_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Store or merge the given user data into the Firestore 'users' collection.
        
        Parameters:
            user_id (str): Identifier for the user; will be trimmed and lowercased for the document ID.
            data (Dict[str, Any]): JSON-serializable mapping of fields to store; fields are merged into the existing document.
        
        Returns:
            bool: `true` if the data was written successfully, `false` otherwise.
        
        Notes:
            - Adds or updates a `last_updated` timestamp and a normalized `user_id` field in the stored document.
            - Uses merge semantics so provided fields are merged with existing document data.
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
        Retrieve a user's stored Firestore document from the 'users' collection.
        
        Parameters:
            user_id (str): User identifier; will be normalized to lowercase and trimmed before lookup.
        
        Returns:
            dict: The user's stored data as a dictionary, or `None` if the document does not exist, Firebase is unavailable, or an error occurs.
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
        Update or add image metadata for a user in Firestore.
        
        Stores the provided image data under the user's `images.{image_hash}` field and updates the user's last-updated timestamp.
        
        Parameters:
            user_id (str): User identifier (will be normalized to a consistent document ID).
            image_hash (str): Unique hash identifying the image; used as the key within the user's images map.
            image_data (Dict[str, Any]): Attributes and metadata for the image to store.
        
        Returns:
            bool: `true` if the update succeeded, `false` otherwise.
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
        Deletes a user's document from the Firestore 'users' collection.
        
        The provided `user_id` is normalized to lowercase and trimmed before locating the document. If Firebase is not available or an error occurs, the operation will fail safely.
        
        Parameters:
            user_id (str): Unique identifier for the user; will be normalized to lowercase and trimmed.
        
        Returns:
            True if deletion succeeded, False otherwise.
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
        Retrieve up to `limit` user document IDs from the 'users' collection.
        
        Parameters:
            limit (int): Maximum number of user IDs to return.
        
        Returns:
            List[str]: A list of user document IDs (may be empty).
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
        Write a user's Firestore document to a local JSON file.
        
        If no data exists for the given user, the function returns False. The function ensures the target directory exists and serializes Firestore timestamp-like values as strings when writing JSON.
        
        Parameters:
            user_id (str): Identifier of the user whose data will be backed up.
            file_path (str): Destination file path (including filename) for the JSON backup.
        
        Returns:
            bool: `True` if the user data was successfully written to the file, `False` otherwise.
        """
        logger.info(f"Backing up user {user_id} to {file_path}")
        data = self.get_user_data(user_id)
        if not data:
            logger.warning(f"No data to backup for user: {user_id}")
            return False
        
        try:
            # Convert Firestore timestamps to strings for JSON serialization
            def convert_timestamps(obj):
                """
                Extracts a timestamp value from an object when available.
                
                Parameters:
                    obj: The object to inspect; if it has a `timestamp` attribute callable as `obj.timestamp()`, that call's result is returned.
                
                Returns:
                    The value returned by `obj.timestamp()` when `obj` provides that method, otherwise the original `obj`.
                """
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
        Restore a user's Firestore document from a local JSON file.
        
        Parameters:
            user_id (str): Identifier of the user whose document will be restored.
            file_path (str): Path to the local JSON file containing the user data.
        
        Returns:
            `true` if the user data was stored successfully in Firestore, `false` otherwise.
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
    """
    Return the module-level FirebaseService singleton.
    
    Returns:
        firebase_service (FirebaseService): The shared FirebaseService instance used for Firestore operations.
    """
    return firebase_service