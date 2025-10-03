import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app


class TestRoutes:
    """Test API routes"""

    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert "/api/v1/attribute_clothes" in data["endpoints"]
        assert "/api/v1/styler" in data["endpoints"]
        assert "/api/v1/health" in data["endpoints"]

    @patch(
        "app.services.attribution_service.ClothingAttributionService.process_images_for_attributes"
    )
    def test_attribute_clothes_missing_user_id(self, mock_process):
        """Test attribute_clothes endpoint requires user_id"""
        # Missing user_id parameter
        response = self.client.post("/api/v1/attribute_clothes")

        assert response.status_code == 422  # Validation error

    @patch("app.services.styler_service.StylerService.generate_outfit_recommendation")
    def test_styler_missing_user_id(self, mock_generate):
        """Test styler endpoint requires user_id"""
        # Missing user_id parameter
        response = self.client.post("/api/v1/styler")

        assert response.status_code == 422  # Validation error

    @patch("app.services.styler_service.StylerService.generate_outfit_recommendation")
    def test_styler_with_valid_params(self, mock_generate):
        """Test styler endpoint with valid parameters"""
        # Mock the service response
        mock_response = {
            "success": True,
            "message": "Outfit generated successfully",
            "user_id": "test_user",
            "styling_timestamp": "2023-01-01T00:00:00",
            "request_parameters": {
                "city": "Toronto",
                "weather": "cold weather",
                "occasion": "work",
            },
            "outfit_recommendation": {"top": "shirt.jpg"},
            "available_items_count": 5,
        }
        mock_generate.return_value = mock_response

        response = self.client.post(
            "/api/v1/styler",
            params={
                "user_id": "test_user",
                "city": "Toronto",
                "weather": "cold weather",
                "occasion": "work",
            },
        )

        assert response.status_code == 200
        # Note: The actual service call is mocked, so we're testing the endpoint structure
