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
    """
    Provide current service health information.
    
    Returns:
        HealthResponse: Object containing a `status` string (set to "healthy") and a `timestamp` string in ISO 8601 format representing the current time.
    """
    return HealthResponse(status="healthy", timestamp=datetime.now().isoformat())


@router.get("/storage-info")
async def storage_info() -> Dict[str, Any]:
    """
    Return configuration details of the image storage service.
    
    The returned dictionary contains storage configuration and metadata provided by the active image storage implementation (for example: provider name, bucket or container identifier, root path/prefix, and other service-specific options).
    
    Returns:
        storage_info (Dict[str, Any]): Storage configuration and metadata.
    """
    image_storage = get_image_storage_service()
    return image_storage.get_storage_info()


@router.post("/attribute_clothes", response_model=AttributeAnalysisResponse)
async def attribute_clothes(user_id: str, files: List[UploadFile] = File(...)):
    """
    Analyze uploaded images to extract clothing attributes and store results per user.
    
    Processes the provided image files, saves attribute data to a user-specific JSON file, and returns the combined analysis for each image.
    
    Parameters:
        user_id (str): Identifier used to associate and store the analysis with a specific user.
        files (List[UploadFile]): Uploaded image files to be analyzed.
    
    Returns:
        AttributeAnalysisResponse: Analysis results for each provided image.
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