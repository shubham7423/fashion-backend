import pytest
from app.core.config import Settings, settings


class TestConfig:
    """Test configuration settings"""

    def test_default_settings(self):
        """Test default configuration values"""
        assert settings.APP_NAME == "Fashion Backend API"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.MAX_FILE_SIZE == 10 * 1024 * 1024  # 10MB
        assert settings.TARGET_WIDTH == 512
        assert settings.TARGET_HEIGHT == 512
        assert settings.JPEG_QUALITY == 85
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

    def test_allowed_extensions(self):
        """Test allowed file extensions"""
        expected_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".avif",
        }
        assert settings.ALLOWED_EXTENSIONS == expected_extensions

    def test_image_settings(self):
        """Test image processing settings"""
        assert settings.MAINTAIN_ASPECT_RATIO is True
        assert settings.SAVE_IMAGES is True
        assert settings.SAVE_PROCESSED is True
        assert settings.SAVE_ORIGINAL is False

    def test_storage_settings(self):
        """Test storage settings"""
        assert settings.IMAGES_DIRECTORY == "saved_images"
        assert settings.ATTRIBUTES_JSON_FILE == "image_attributes.json"
        assert settings.USER_DATA_DIRECTORY == "user_data"
        assert settings.CREATE_USER_SUBDIRS is True
        assert settings.AVOID_DUPLICATES is True

    def test_custom_settings_creation(self):
        """Test creating custom settings"""
        custom_settings = Settings(
            APP_NAME="Custom App",
            MAX_FILE_SIZE=5 * 1024 * 1024,  # 5MB
            TARGET_WIDTH=256,
        )

        assert custom_settings.APP_NAME == "Custom App"
        assert custom_settings.MAX_FILE_SIZE == 5 * 1024 * 1024
        assert custom_settings.TARGET_WIDTH == 256
        # Default values should still be present
        assert custom_settings.JPEG_QUALITY == 85
