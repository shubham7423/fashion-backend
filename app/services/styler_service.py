from fastapi import HTTPException
from pathlib import Path
from app.core.config import settings
from app.models.response import StylerResponse
from app.services.styler.gemini_styler import GeminiStyler
from app.services.styler.openai_styler import OpenAIStyler
from app.core.user_id_utils import normalize_user_id
from app.core.data_service import get_data_service
from app.core.logging_config import get_logger
from datetime import datetime
from typing import Dict, Any, List
import json
import os


class StylerService:
    """Service for generating outfit recommendations based on user's clothing attributes"""

    @staticmethod
    def get_user_json_file_path(user_id: str) -> Path:
        """Get the path to user's JSON file containing image attributes"""
        # Normalize and validate user_id for safe filesystem usage
        normalized_user_id = normalize_user_id(user_id)
        
        if settings.CREATE_USER_SUBDIRS:
            user_dir = Path(settings.USER_DATA_DIRECTORY) / normalized_user_id
            json_path = user_dir / settings.ATTRIBUTES_JSON_FILE
        else:
            json_path = Path(f"{normalized_user_id}_{settings.ATTRIBUTES_JSON_FILE}")
            
        return json_path

    @staticmethod
    def load_user_attributes(user_id: str) -> Dict[str, Any]:
        """Load user's clothing attributes using unified data service"""
        data_service = get_data_service()
        user_data = data_service.load_user_data(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail=f"No clothing data found for user '{user_id}'. Please upload some images first using /attribute_clothes endpoint.",
            )
        
        return user_data

    @staticmethod
    def extract_clothing_attributes_for_styling(
        user_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract only the clothing attributes needed for styling recommendations"""
        styling_attributes = []

        images_data = user_data.get("images", {})

        for image_hash, image_data in images_data.items():
            attributes = image_data.get("attributes", {})

            # Only include items that have valid attributes and are not duplicates
            if attributes and isinstance(attributes, dict):
                # Create a clean attribute object for styling
                styling_item = {
                    "image": attributes.get(
                        "image", image_data.get("filename", f"image_{image_hash[:8]}")
                    ),
                    "identifier": attributes.get("identifier", "unknown"),
                    "category": attributes.get("category", "unknown"),
                    "gender": attributes.get("gender", "unisex"),
                    "primary_color": attributes.get("primary_color", "unknown"),
                    "style": attributes.get("style", "casual"),
                    "occasion": attributes.get("occasion", "everyday"),
                    "weather": attributes.get("weather", "mild"),
                    "fit": attributes.get("fit", "regular"),
                    "description": attributes.get("description", "clothing item"),
                }

                # Only include if it has essential information
                if (
                    styling_item["identifier"] != "unknown"
                    and styling_item["category"] != "unknown"
                ):
                    styling_attributes.append(styling_item)

        return styling_attributes

    @staticmethod
    def get_outfit_image_urls(
        outfit_recommendation: dict, 
        user_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate download URLs for outfit recommendation images.
        
        Args:
            outfit_recommendation: Recommended outfit items
            user_data: User's stored clothing data
            
        Returns:
            Dictionary mapping item types to download URLs
        """
        logger = get_logger(__name__)
        from app.core.image_storage_service import get_image_storage_service
        
        outfit_urls = {}
        image_storage = get_image_storage_service()
        images_data = user_data.get("images", {})
        
        logger.debug(f"Generating download URLs for outfit items | Available images: {len(images_data)}")
        
        # Map outfit items to download URLs
        outfit_items = {
            "top": outfit_recommendation.get("top"),
            "bottom": outfit_recommendation.get("bottom"),
            "outerwear": outfit_recommendation.get("outerwear"),
        }
        
        for item_type, filename in outfit_items.items():
            if not filename:
                logger.debug(f"No {item_type} specified in outfit recommendation")
                continue
                
            logger.debug(f"Looking for download URL for {item_type}: {filename}")
            
            # Find the image data by filename
            found = False
            for image_hash, image_data in images_data.items():
                stored_filename = image_data.get("filename", "")
                saved_images = image_data.get("saved_images", {})
                
                # Check if this is the correct image by filename
                if (stored_filename == filename or 
                    filename in stored_filename or 
                    any(filename in path for path in saved_images.values())):
                    
                    # Get download URL for processed image
                    processed_path = saved_images.get("processed")
                    if processed_path:
                        download_url = image_storage.get_download_url(processed_path)
                        if download_url:
                            outfit_urls[item_type] = download_url
                            storage_type = "GCS" if download_url.startswith("https://") else "Local"
                            logger.debug(f"✅ Generated {storage_type} download URL for {item_type}: {filename}")
                            found = True
                            break
                        else:
                            logger.warning(f"Failed to generate download URL for {item_type}: {filename}")
                    else:
                        logger.warning(f"No processed image path found for {item_type}: {filename}")
            
            if not found:
                logger.warning(f"Could not find image data for {item_type}: {filename}")
        
        logger.info(f"Generated {len(outfit_urls)} download URLs for outfit items")
        return outfit_urls

    @staticmethod
    async def generate_outfit_recommendation(
        user_id: str,
        city: str = "Toronto",
        weather: str = "early fall weather - expect temperatures around 15-20°C, partly cloudy",
        occasion: str = "casual day out",
    ) -> StylerResponse:
        """
        Generate outfit recommendation for the user based on their clothing attributes

        Args:
            user_id: Unique identifier for the user
            city: City for the occasion (default: "Toronto")
            weather: Weather conditions (default: fall weather)
            occasion: The occasion type (default: "casual day out")

        Returns:
            StylerResponse with outfit recommendation
        """
        logger = get_logger(__name__)
        logger.info(f"[user={user_id}] 👔 Starting outfit recommendation | City: {city} | Weather: {weather} | Occasion: {occasion}")
        
        try:
            # Load user's clothing data
            logger.debug(f"[user={user_id}] Loading user clothing data")
            user_data = StylerService.load_user_attributes(user_id)

            # Extract clothing attributes for styling
            logger.debug(f"[user={user_id}] Extracting clothing attributes for styling")
            clothing_attributes = StylerService.extract_clothing_attributes_for_styling(
                user_data
            )

            if not clothing_attributes:
                logger.warning(f"[user={user_id}] No valid clothing items found")
                return StylerResponse(
                    success=False,
                    message=f"No valid clothing items found for user '{user_id}'. Please upload some images with valid clothing items first.",
                    user_id=user_id,
                    styling_timestamp=datetime.now().isoformat(),
                    request_parameters={
                        "city": city,
                        "weather": weather,
                        "occasion": occasion,
                    },
                    available_items_count=0,
                    error="No valid clothing items available for styling",
                )

            logger.info(f"[user={user_id}] Found {len(clothing_attributes)} clothing items for styling")

            # Initialize the styler based on configuration
            try:
                styler_type = settings.DEFAULT_STYLER.lower()
                logger.debug(f"[user={user_id}] Initializing {styler_type} styler")
                
                if styler_type == "openai":
                    styler = OpenAIStyler()
                else:
                    # Default to Gemini
                    styler = GeminiStyler()
            except ValueError as e:
                logger.error(f"[user={user_id}] Styler initialization failed: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Styler initialization failed: {str(e)}"
                )

            # Generate outfit recommendation
            try:
                logger.info(f"[user={user_id}] 🧠 Generating AI outfit recommendation using {styler_type}")
                outfit_json = styler.style(
                    clothing_attributes=clothing_attributes,
                    city=city,
                    weather=weather,
                    occasion=occasion,
                )

                # Parse the outfit recommendation
                outfit_recommendation = (
                    json.loads(outfit_json)
                    if isinstance(outfit_json, str)
                    else outfit_json
                )

                logger.debug(f"[user={user_id}] AI outfit recommendation generated successfully")

                # Get download URLs for outfit items
                logger.debug(f"[user={user_id}] Generating download URLs for outfit images")
                outfit_image_urls = StylerService.get_outfit_image_urls(
                    outfit_recommendation, user_data
                )

                # Log the recommended outfit
                outfit_summary = {
                    "top": outfit_recommendation.get("top", "None"),
                    "bottom": outfit_recommendation.get("bottom", "None"),
                    "outerwear": outfit_recommendation.get("outerwear", "None")
                }
                logger.info(f"[user={user_id}] ✅ Outfit recommendation complete | Top: {outfit_summary['top']} | Bottom: {outfit_summary['bottom']} | Outerwear: {outfit_summary['outerwear']} | URLs: {len(outfit_image_urls)}")

                return StylerResponse(
                    success=True,
                    message=f"Outfit recommendation generated successfully for user '{user_id}'",
                    user_id=user_id,
                    styling_timestamp=datetime.now().isoformat(),
                    request_parameters={
                        "city": city,
                        "weather": weather,
                        "occasion": occasion,
                    },
                    outfit_recommendation=outfit_recommendation,
                    available_items_count=len(clothing_attributes),
                    outfit_images=outfit_image_urls,
                )

            except Exception as e:
                logger.error(f"[user={user_id}] Failed to generate outfit recommendation: {e}")
                return StylerResponse(
                    success=False,
                    message=f"Failed to generate outfit recommendation for user '{user_id}'",
                    user_id=user_id,
                    styling_timestamp=datetime.now().isoformat(),
                    request_parameters={
                        "city": city,
                        "weather": weather,
                        "occasion": occasion,
                    },
                    available_items_count=len(clothing_attributes),
                    error=f"Styling error: {str(e)}",
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[user={user_id}] Unexpected error in outfit generation: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error in outfit generation: {str(e)}",
            )

    @staticmethod
    def validate_styling_parameters(
        city: str, weather: str, occasion: str
    ) -> Dict[str, str]:
        """Validate and sanitize styling parameters"""
        # Basic validation and sanitization
        validated_params = {
            "city": city.strip() if city else "Toronto",
            "weather": (
                weather.strip()
                if weather
                else "early fall weather - expect temperatures around 15-20°C, partly cloudy"
            ),
            "occasion": occasion.strip() if occasion else "casual day out",
        }

        # Ensure parameters are not too long (security measure)
        max_length = 200
        for key, value in validated_params.items():
            if len(value) > max_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Parameter '{key}' is too long. Maximum length is {max_length} characters.",
                )

        return validated_params
