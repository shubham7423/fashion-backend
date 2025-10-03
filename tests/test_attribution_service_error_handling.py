import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from PIL import Image
import io
from app.services.attribution_service import ClothingAttributionService
from app.models.response import ImageInfo, ImageAnalysisResult


class TestAttributionServiceErrorHandling:
    """Test error handling in ClothingAttributionService"""

    @pytest.mark.asyncio
    @patch(
        "app.services.attribution_service.ClothingAttributionService.extract_clothing_attributes"
    )
    async def test_gemini_error_response_handling(self, mock_extract):
        """Test that Gemini error responses are properly handled"""
        # Mock the extract method to return an error response
        mock_extract.return_value = {
            "error": "Failed to extract attributes using Gemini: API rate limit exceeded"
        }

        # Create a mock file
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"fake_image_data"
        mock_file.seek = AsyncMock()
        mock_file.close = AsyncMock()

        # Mock other dependencies
        with patch(
            "app.services.attribution_service.ClothingAttributionService.validate_image_file",
            return_value=True,
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.validate_file_size",
            return_value=1024,
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.calculate_image_hash",
            return_value="test_hash",
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.is_duplicate_image",
            return_value=(False, {}),
        ), patch(
            "PIL.Image.open"
        ) as mock_image_open, patch(
            "app.services.attribution_service.ClothingAttributionService.compress_and_resize_image",
            return_value=(Mock(), {}),
        ), patch(
            "app.services.attribution_service.settings.SAVE_IMAGES", False
        ):

            # Mock PIL Image
            mock_image = Mock(spec=Image.Image)
            mock_image_open.return_value = mock_image

            result = await ClothingAttributionService.process_single_image_analysis(
                mock_file, "test_user"
            )

            # Verify error handling
            assert isinstance(result, ImageAnalysisResult)
            assert result.status == "attributes_failed"
            assert (
                result.error
                == "Failed to extract attributes using Gemini: API rate limit exceeded"
            )
            assert result.attributes is None

            # Verify file pointer was reset
            mock_file.seek.assert_called_with(0)

    @pytest.mark.asyncio
    @patch(
        "app.services.attribution_service.ClothingAttributionService.extract_clothing_attributes"
    )
    async def test_invalid_gemini_response_handling(self, mock_extract):
        """Test that invalid Gemini responses (non-dict) are properly handled"""
        # Mock the extract method to return a non-dict response
        mock_extract.return_value = "invalid response"

        # Create a mock file
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"fake_image_data"
        mock_file.seek = AsyncMock()
        mock_file.close = AsyncMock()

        # Mock other dependencies
        with patch(
            "app.services.attribution_service.ClothingAttributionService.validate_image_file",
            return_value=True,
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.validate_file_size",
            return_value=1024,
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.calculate_image_hash",
            return_value="test_hash",
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.is_duplicate_image",
            return_value=(False, {}),
        ), patch(
            "PIL.Image.open"
        ) as mock_image_open, patch(
            "app.services.attribution_service.ClothingAttributionService.compress_and_resize_image",
            return_value=(Mock(), {}),
        ), patch(
            "app.services.attribution_service.settings.SAVE_IMAGES", False
        ):

            # Mock PIL Image
            mock_image = Mock(spec=Image.Image)
            mock_image_open.return_value = mock_image

            result = await ClothingAttributionService.process_single_image_analysis(
                mock_file, "test_user"
            )

            # Verify error handling
            assert isinstance(result, ImageAnalysisResult)
            assert result.status == "attributes_failed"
            assert (
                "Invalid Gemini response format: expected dict, got str" in result.error
            )
            assert result.attributes is None

            # Verify file pointer was reset
            mock_file.seek.assert_called_with(0)

    @pytest.mark.asyncio
    @patch(
        "app.services.attribution_service.ClothingAttributionService.extract_clothing_attributes"
    )
    @patch(
        "app.services.attribution_service.ClothingAttributionService.save_attributes_to_json"
    )
    async def test_successful_response_still_saves(self, mock_save_json, mock_extract):
        """Test that successful responses still save to JSON as before"""
        # Mock the extract method to return a successful response
        mock_extract.return_value = {
            "identifier": "top",
            "category": "T-Shirt",
            "primary_color": "blue",
        }

        # Create a mock file
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"fake_image_data"
        mock_file.seek = AsyncMock()
        mock_file.close = AsyncMock()

        # Mock other dependencies
        with patch(
            "app.services.attribution_service.ClothingAttributionService.validate_image_file",
            return_value=True,
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.validate_file_size",
            return_value=1024,
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.calculate_image_hash",
            return_value="test_hash",
        ), patch(
            "app.services.attribution_service.ClothingAttributionService.is_duplicate_image",
            return_value=(False, {}),
        ), patch(
            "PIL.Image.open"
        ) as mock_image_open, patch(
            "app.services.attribution_service.ClothingAttributionService.compress_and_resize_image",
            return_value=(Mock(), {}),
        ), patch(
            "app.services.attribution_service.settings.SAVE_IMAGES", False
        ):

            # Mock PIL Image
            mock_image = Mock(spec=Image.Image)
            mock_image_open.return_value = mock_image

            result = await ClothingAttributionService.process_single_image_analysis(
                mock_file, "test_user"
            )

            # Verify successful processing
            assert isinstance(result, ImageAnalysisResult)
            assert result.status == "attributes_extracted"
            assert result.error is None
            assert result.attributes is not None
            assert result.attributes["identifier"] == "top"

            # Verify JSON was saved
            mock_save_json.assert_called_once()

            # Verify file pointer was reset
            mock_file.seek.assert_called_with(0)
