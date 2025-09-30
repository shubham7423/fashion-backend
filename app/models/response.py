from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ImageInfo(BaseModel):
    """Image information model"""

    filename: str
    content_type: str
    file_size_bytes: int
    file_size_mb: float


class ImageAnalysisResult(BaseModel):
    """Analysis result for a single image"""
    
    image_info: ImageInfo
    status: str = "ready_for_processing"
    attributes: Optional[dict] = None
    error: Optional[str] = None


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


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool = False
    error: str
    detail: Optional[str] = None
