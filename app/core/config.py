from pydantic_settings import BaseSettings
from typing import Set
import os

class Settings(BaseSettings):
    """Application settings"""

    APP_NAME: str = "Fashion Backend API"
    APP_DESCRIPTION: str = (
        "API for processing fashion images and analyzing clothing attributes"
    )
    APP_VERSION: str = "1.0.0"

    # Image validation settings
    ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".avif"}
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Image processing settings
    TARGET_WIDTH: int = 512  # Target width for clothing recognition
    TARGET_HEIGHT: int = 512  # Target height for clothing recognition
    JPEG_QUALITY: int = 85  # JPEG compression quality (1-100)
    MAINTAIN_ASPECT_RATIO: bool = True  # Keep original aspect ratio when resizing

    # Image storage settings
    SAVE_IMAGES: bool = True  # Whether to save processed images
    IMAGES_DIRECTORY: str = "saved_images"  # Directory to save images
    SAVE_ORIGINAL: bool = False  # Save original images
    SAVE_PROCESSED: bool = True  # Save processed/compressed images
    
    # JSON storage settings
    SAVE_ATTRIBUTES_JSON: bool = True  # Whether to save attributes to JSON file
    ATTRIBUTES_JSON_FILE: str = "image_attributes.json"  # JSON file to store attributes
    AVOID_DUPLICATES: bool = True  # Whether to avoid saving duplicate images

    # API keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
