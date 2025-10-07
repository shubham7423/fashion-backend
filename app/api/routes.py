from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from app.services.attribution_service import ClothingAttributionService
from app.services.styler_service import StylerService
from app.core.image_storage_service import get_image_storage_service
from app.models.response import (
    AttributeAnalysisResponse,
    HealthResponse,
    StylerResponse,
)
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", timestamp=datetime.now().isoformat())


@router.get("/storage-info")
async def storage_info() -> Dict[str, Any]:
    """Get information about the current storage configuration"""
    image_storage = get_image_storage_service()
    return image_storage.get_storage_info()


@router.post("/attribute_clothes", response_model=AttributeAnalysisResponse)
async def attribute_clothes(user_id: str, files: List[UploadFile] = File(...)):
    """
    Process uploaded image files for clothing attribute analysis

    This endpoint receives one or more image files and processes them to extract
    clothing attributes. Images are stored per user and attributes are saved
    to user-specific JSON files.

    Args:
        user_id: Unique identifier for the user (required)
        files: List of image files to be processed

    Returns:
        JSON response with analysis results for all images
    """
    return await ClothingAttributionService.process_images_for_attributes(
        files, user_id
    )


@router.post("/styler", response_model=StylerResponse)
async def styler(
    user_id: str,
    city: str = Query(default="Toronto", description="City for the occasion"),
    weather: str = Query(
        default="early fall weather - expect temperatures around 15-20°C, partly cloudy",
        description="Weather conditions",
    ),
    occasion: str = Query(default="casual day out", description="The occasion type"),
):
    """
    Generate outfit recommendations based on user's stored clothing attributes

    This endpoint analyzes the user's clothing collection (stored from previous
    /attribute_clothes uploads) and generates outfit recommendations suitable
    for the specified city, weather, and occasion.

    Args:
        user_id: Unique identifier for the user (required)
        city: City for the occasion (default: "Toronto")
        weather: Weather conditions (default: fall weather description)
        occasion: The occasion type (default: "casual day out")

    Returns:
        JSON response with outfit recommendation including:
        - Selected clothing items (top, bottom, outerwear)
        - Styling justification and tips
        - Weather considerations
        - Accessory recommendations
    """
    # Validate parameters
    validated_params = StylerService.validate_styling_parameters(
        city, weather, occasion
    )

    return await StylerService.generate_outfit_recommendation(
        user_id=user_id,
        city=validated_params["city"],
        weather=validated_params["weather"],
        occasion=validated_params["occasion"],
    )
