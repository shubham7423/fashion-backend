from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.attribution_service import ClothingAttributionService
from app.models.response import AttributeAnalysisResponse, HealthResponse
from datetime import datetime
from typing import List

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", timestamp=datetime.now().isoformat())


@router.post("/attribute_clothes", response_model=AttributeAnalysisResponse)
async def attribute_clothes(files: List[UploadFile] = File(...)):
    """
    Process uploaded image files for clothing attribute analysis

    This endpoint receives one or more image files and processes them to extract
    clothing attributes. Images are not stored permanently.

    Args:
        files: List of image files to be processed

    Returns:
        JSON response with analysis results for all images
    """
    return await ClothingAttributionService.process_images_for_attributes(files)
