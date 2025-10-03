import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from PIL import Image
import io
from app.services.attribution_service import ClothingAttributionService
from app.models.response import ImageInfo, ImageAnalysisResult


class TestClothingAttributionService:
    """Test ClothingAttributionService functionality"""

    def test_validate_image_file_valid(self):
        """Test validation of valid image file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"

        with patch("app.core.config.settings.ALLOWED_EXTENSIONS", {".jpg", ".jpeg"}):
            result = ClothingAttributionService.validate_image_file(mock_file)
            assert result is True

    def test_validate_image_file_invalid_extension(self):
        """Test validation of file with invalid extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"

        with patch("app.core.config.settings.ALLOWED_EXTENSIONS", {".jpg", ".jpeg"}):
            result = ClothingAttributionService.validate_image_file(mock_file)
            assert result is False

    def test_validate_image_file_no_filename(self):
        """Test validation of file with no filename"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None

        result = ClothingAttributionService.validate_image_file(mock_file)
        assert result is False

    def test_validate_image_file_invalid_content_type(self):
        """Test validation of file with invalid content type"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "text/plain"

        with patch("app.core.config.settings.ALLOWED_EXTENSIONS", {".jpg", ".jpeg"}):
            result = ClothingAttributionService.validate_image_file(mock_file)
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_file_size_valid(self):
        """Test file size validation for valid size"""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read.return_value = b"x" * 1024  # 1KB file

        with patch("app.core.config.settings.MAX_FILE_SIZE", 10 * 1024 * 1024):  # 10MB
            size = await ClothingAttributionService.validate_file_size(mock_file)
            assert size == 1024

    @pytest.mark.asyncio
    async def test_validate_file_size_too_large(self):
        """Test file size validation for oversized file"""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read.return_value = b"x" * (11 * 1024 * 1024)  # 11MB file

        with patch(
            "app.core.config.settings.MAX_FILE_SIZE", 10 * 1024 * 1024
        ):  # 10MB limit
            with pytest.raises(Exception):  # Should raise HTTPException
                await ClothingAttributionService.validate_file_size(mock_file)

    def test_create_image_info(self):
        """Test ImageInfo creation"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"

        image_info = ClothingAttributionService.create_image_info(mock_file, 2048)

        assert isinstance(image_info, ImageInfo)
        assert image_info.filename == "test.jpg"
        assert image_info.content_type == "image/jpeg"
        assert image_info.file_size_bytes == 2048
        assert image_info.file_size_mb == round(2048 / (1024 * 1024), 2)

    def test_compress_and_resize_image(self):
        """Test image compression and resizing"""
        # Create a test image
        test_image = Image.new("RGB", (800, 600), color="red")

        with patch("app.core.config.settings.TARGET_WIDTH", 512):
            with patch("app.core.config.settings.TARGET_HEIGHT", 512):
                with patch("app.core.config.settings.MAINTAIN_ASPECT_RATIO", True):
                    processed_image, info = (
                        ClothingAttributionService.compress_and_resize_image(test_image)
                    )

        # Check that image was processed
        assert isinstance(processed_image, Image.Image)
        assert isinstance(info, dict)
        assert "original_size" in info
        assert info["original_size"] == (800, 600)

    def test_compress_and_resize_image_rgb_conversion(self):
        """Test RGB conversion during compression"""
        # Create a RGBA test image (needs conversion)
        test_image = Image.new("RGBA", (400, 300), color=(255, 0, 0, 128))

        processed_image, info = ClothingAttributionService.compress_and_resize_image(
            test_image
        )

        # Should be converted to RGB
        assert processed_image.mode == "RGB"
