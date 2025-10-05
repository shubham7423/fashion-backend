"""Test fixtures for image-related tests."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from fastapi import UploadFile
from PIL import Image
import io
import pytest


class ImageTestFixtures:
    """Collection of image-related test fixtures and utilities."""

    @staticmethod
    def create_test_image(color="red", size=(100, 100), format="JPEG"):
        """Create a simple test image with specified color and format."""
        img = Image.new("RGB", size, color=color)
        
        # Save to bytes buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format=format)
        img_buffer.seek(0)
        
        return img_buffer.getvalue()

    @staticmethod
    def create_test_image_file(color="red", size=(100, 100), filename="test.jpg"):
        """Create a test image file on disk."""
        img = Image.new("RGB", size, color=color)
        temp_file = tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False)
        img.save(temp_file.name, "JPEG")
        return temp_file.name

    @staticmethod
    def create_mock_upload_file(
        filename="test.jpg",
        content_type="image/jpeg",
        file_size=1024,
        file_content=None
    ):
        """Create a mock UploadFile for testing."""
        if file_content is None:
            file_content = ImageTestFixtures.create_test_image()
        
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.size = file_size
        mock_file.read.return_value = file_content
        mock_file.seek = AsyncMock()
        mock_file.close = AsyncMock()
        
        return mock_file

    @staticmethod
    def create_mock_pil_image(size=(512, 512), mode="RGB", color="red"):
        """Create a mock PIL Image for testing."""
        mock_image = Mock(spec=Image.Image)
        mock_image.size = size
        mock_image.mode = mode
        mock_image.resize.return_value = mock_image
        mock_image.convert.return_value = mock_image
        return mock_image


@pytest.fixture
def sample_image_data():
    """Pytest fixture for sample image data."""
    return ImageTestFixtures.create_test_image()


@pytest.fixture
def mock_upload_file():
    """Pytest fixture for mock upload file."""
    return ImageTestFixtures.create_mock_upload_file()


@pytest.fixture
def mock_pil_image():
    """Pytest fixture for mock PIL image."""
    return ImageTestFixtures.create_mock_pil_image()


@pytest.fixture
def test_image_attributes():
    """Pytest fixture for test image attributes."""
    return {
        "identifier": "top",
        "category": "T-Shirt",
        "gender": "men",
        "primary_color": "blue",
        "secondary_color": "white",
        "style": "casual",
        "material": "cotton",
        "pattern": "solid",
        "fit": "regular",
        "sleeve_length": "short",
        "neckline": "round"
    }


@pytest.fixture
def test_user_data():
    """Pytest fixture for test user data."""
    return {
        "images": {
            "hash1": {
                "filename": "shirt.jpg",
                "attributes": {
                    "image": "shirt.jpg",
                    "identifier": "top",
                    "category": "T-Shirt",
                    "gender": "men",
                    "primary_color": "blue",
                    "style": "casual"
                }
            },
            "hash2": {
                "filename": "pants.jpg",
                "attributes": {
                    "image": "pants.jpg",
                    "identifier": "bottom",
                    "category": "Jeans",
                    "gender": "men",
                    "primary_color": "navy"
                }
            }
        }
    }
