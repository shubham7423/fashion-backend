from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class ImageInfo(BaseModel):
    """Image information model"""

    filename: str
    content_type: str
    file_size_bytes: int
    file_size_mb: float
    download_url: Optional[str] = None


class ImageAnalysisResult(BaseModel):
    """Analysis result for a single image"""

    image_info: ImageInfo
    status: str = "ready_for_processing"
    attributes: Optional[dict] = None
    error: Optional[str] = None
    image_url: Optional[str] = None


class AttributeAnalysisResponse(BaseModel):
    """Response model for clothing attribute analysis"""

    success: bool
    message: str
    processing_timestamp: str
    total_images: int
    successful_analyses: int
    failed_analyses: int
    results: List[ImageAnalysisResult]


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    timestamp: str


class StylerResponse(BaseModel):
    """Response model for outfit styling recommendations"""

    success: bool
    message: str
    user_id: str
    styling_timestamp: str
    request_parameters: dict
    outfit_recommendation: Optional[dict] = None
    available_items_count: int
    error: Optional[str] = None
    outfit_images: Optional[Dict[str, str]] = None  # Map of item type to download URL


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool = False
    error: str
    detail: Optional[str] = None
