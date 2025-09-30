from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ImageInfo(BaseModel):
    """Image information model"""

    filename: str
    content_type: str
    file_size_bytes: int
    file_size_mb: float


class AttributeAnalysisResponse(BaseModel):
    """Response model for clothing attribute analysis"""

    success: bool
    message: str
    image_info: ImageInfo
    processing_timestamp: str
    status: str = "ready_for_processing"

    # Placeholder for future attribute analysis results
    attributes: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool = False
    error: str
    detail: Optional[str] = None
