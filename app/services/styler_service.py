from fastapi import HTTPException
from pathlib import Path
from app.core.config import settings
from app.models.response import StylerResponse
from app.services.styler.gemini_styler import GeminiStyler
from app.services.styler.openai_styler import OpenAIStyler
from app.core.user_id_utils import normalize_user_id
from datetime import datetime
from typing import Dict, Any, List
import json
import os


class StylerService:
    """Service for generating outfit recommendations based on user's clothing attributes"""

    @staticmethod
    def get_user_json_file_path(user_id: str) -> Path:
        """Get the path to user's JSON file containing image attributes"""
        # Normalize and validate user_id ONCE here
        normalized_user_id = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
        if settings.CREATE_USER_SUBDIRS:
            user_dir = Path(settings.USER_DATA_DIRECTORY) / normalized_user_id
            json_path = user_dir / settings.ATTRIBUTES_JSON_FILE
        else:
            json_path = Path(f"{normalized_user_id}_{settings.ATTRIBUTES_JSON_FILE}")
        # Ensure the resolved path is a descendant of the base directory
        base = Path(settings.USER_DATA_DIRECTORY).resolve()
        candidate = json_path.resolve()
        if not str(candidate).startswith(str(base)):
            raise HTTPException(
                status_code=400, detail="User ID resolves outside allowed directory."
            )
        return json_path

    @staticmethod
    def load_user_attributes(user_id: str) -> Dict[str, Any]:
        """Load user's clothing attributes from their JSON file"""
        json_file_path = StylerService.get_user_json_file_path(user_id)
        if not json_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No clothing data found for user '{user_id}'. Please upload some images first using /attribute_clothes endpoint.",
            )
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reading user data: Invalid JSON format in user's clothing data file.",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error loading user data: {str(e)}"
            )

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
        try:
            # Load user's clothing data
            user_data = StylerService.load_user_attributes(user_id)

            # Extract clothing attributes for styling
            clothing_attributes = StylerService.extract_clothing_attributes_for_styling(
                user_data
            )

            if not clothing_attributes:
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

            # Initialize the styler based on configuration
            try:
                if settings.DEFAULT_STYLER.lower() == "openai":
                    styler = OpenAIStyler()
                else:
                    # Default to Gemini
                    styler = GeminiStyler()
            except ValueError as e:
                raise HTTPException(
                    status_code=500, detail=f"Styler initialization failed: {str(e)}"
                )

            # Generate outfit recommendation
            try:
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
                )

            except Exception as e:
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
