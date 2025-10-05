import pytest
from app.models.response import (
    ImageInfo,
    ImageAnalysisResult,
    AttributeAnalysisResponse,
    HealthResponse,
    StylerResponse,
    ErrorResponse,
)


@pytest.mark.unit
@pytest.mark.model
class TestModels:
    """Test Pydantic models"""

    def test_image_info_creation(self):
        """Test ImageInfo model creation"""
        image_info = ImageInfo(
            filename="test.jpg",
            content_type="image/jpeg",
            file_size_bytes=1024,
            file_size_mb=0.001,
        )
        assert image_info.filename == "test.jpg"
        assert image_info.content_type == "image/jpeg"
        assert image_info.file_size_bytes == 1024
        assert image_info.file_size_mb == 0.001

    def test_image_analysis_result_creation(self):
        """Test ImageAnalysisResult model creation"""
        image_info = ImageInfo(
            filename="test.jpg",
            content_type="image/jpeg",
            file_size_bytes=1024,
            file_size_mb=0.001,
        )

        result = ImageAnalysisResult(
            image_info=image_info,
            status="processed",
            attributes={"category": "T-Shirt", "color": "blue"},
        )

        assert result.image_info.filename == "test.jpg"
        assert result.status == "processed"
        assert result.attributes["category"] == "T-Shirt"
        assert result.error is None

    def test_health_response_creation(self):
        """Test HealthResponse model creation"""
        health = HealthResponse(status="healthy", timestamp="2023-01-01T00:00:00")
        assert health.status == "healthy"
        assert health.timestamp == "2023-01-01T00:00:00"

    def test_styler_response_creation(self):
        """Test StylerResponse model creation"""
        styler_response = StylerResponse(
            success=True,
            message="Outfit generated",
            user_id="test_user",
            styling_timestamp="2023-01-01T00:00:00",
            request_parameters={"city": "Toronto"},
            outfit_recommendation={"top": "shirt.jpg"},
            available_items_count=5,
        )

        assert styler_response.success is True
        assert styler_response.user_id == "test_user"
        assert styler_response.available_items_count == 5
        assert styler_response.outfit_recommendation["top"] == "shirt.jpg"

    def test_error_response_creation(self):
        """Test ErrorResponse model creation"""
        error_response = ErrorResponse(error="Test error", detail="Error details")

        assert error_response.success is False
        assert error_response.error == "Test error"
        assert error_response.detail == "Error details"
