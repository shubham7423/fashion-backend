from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.image_service import ImageProcessingService
from app.models.response import AttributeAnalysisResponse, HealthResponse
from datetime import datetime

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", timestamp=datetime.now().isoformat())


@router.post("/attribute_clothes", response_model=AttributeAnalysisResponse)
async def attribute_clothes(file: UploadFile = File(...)):
    """
    Process uploaded image file for clothing attribute analysis

    This endpoint receives an image file and processes it to extract
    clothing attributes. The image is not stored permanently.

    Args:
        file: The image file to be processed

    Returns:
        JSON response with image information and processing status
    """
    return await ImageProcessingService.process_image_for_attributes(file)
