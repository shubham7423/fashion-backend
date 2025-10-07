from fastapi import UploadFile, HTTPException
from pathlib import Path
from app.core.config import settings
from app.models.response import (
    ImageInfo,
    AttributeAnalysisResponse,
    ImageAnalysisResult,
)
from app.services.attribution.gemini_attributor import GeminiAttributor
from app.core.user_id_utils import normalize_user_id
from app.core.data_service import get_data_service
from app.core.image_storage_service import get_image_storage_service
from app.core.logging_config import get_logger
from datetime import datetime
from typing import Any, Dict, Tuple, List
import io
import asyncio
import uuid
import os
import json
import hashlib
from PIL import Image, ImageOps


class ClothingAttributionService:
    """Service for processing and analyzing clothing images"""

    def __init__(self):
        self.logger = get_logger(__name__)

    @staticmethod
    def validate_image_file(file: UploadFile) -> bool:
        """Validate if the uploaded file is a valid image"""
        if not file.filename:
            return False

        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            return False

        # Check content type
        if not file.content_type or not file.content_type.startswith("image/"):
            return False

        return True

    @staticmethod
    async def validate_file_size(file: UploadFile) -> int:
        """Validate file size and return the size in bytes"""
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024*1024)}MB",
            )

        # Reset file pointer
        await file.seek(0)
        return file_size

    @staticmethod
    def create_image_info(file: UploadFile, file_size: int) -> ImageInfo:
        """Create ImageInfo object from uploaded file"""
        return ImageInfo(
            filename=file.filename,
            content_type=file.content_type,
            file_size_bytes=file_size,
            file_size_mb=round(file_size / (1024 * 1024), 2),
        )

    @staticmethod
    def compress_and_resize_image(image: Image.Image) -> Tuple[Image.Image, dict]:
        """
        Compress and resize image for optimal clothing recognition

        Resizes image to target dimensions while maintaining aspect ratio
        and applies optimal compression for clothing/texture analysis.

        Args:
            image: PIL Image object

        Returns:
            Tuple of (processed_image, processing_info)
        """
        original_size = image.size
        original_format = image.format or "JPEG"

        # Convert to RGB if necessary (handles RGBA, P mode images)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Calculate new dimensions maintaining aspect ratio
        if settings.MAINTAIN_ASPECT_RATIO:
            # Calculate the scaling factor to fit within target dimensions
            width_ratio = settings.TARGET_WIDTH / original_size[0]
            height_ratio = settings.TARGET_HEIGHT / original_size[1]
            scale_factor = min(width_ratio, height_ratio)

            new_width = int(original_size[0] * scale_factor)
            new_height = int(original_size[1] * scale_factor)
        else:
            new_width = settings.TARGET_WIDTH
            new_height = settings.TARGET_HEIGHT

        # Resize image using high-quality resampling
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Apply additional optimization for clothing recognition
        # Enhance image for better texture and material detection
        resized_image = ImageOps.exif_transpose(resized_image)  # Fix orientation

        processing_info = {
            "original_size": original_size,
            "processed_size": (new_width, new_height),
            "original_format": original_format,
            "scale_factor": scale_factor if settings.MAINTAIN_ASPECT_RATIO else None,
            "compression_quality": settings.JPEG_QUALITY,
            "size_reduction_ratio": round(
                (new_width * new_height) / (original_size[0] * original_size[1]), 3
            ),
        }

        return resized_image, processing_info

    @staticmethod
    def ensure_images_directory(user_id: str = None) -> Path:
        """
        Ensure the images directory exists and return its path

        Args:
            user_id: Optional user ID for user-specific directories

        Returns:
            Path object of the images directory
        """
        # Normalize and validate user_id if provided
        if user_id and settings.CREATE_USER_SUBDIRS:
            user_id = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
            base_dir = Path(settings.USER_DATA_DIRECTORY) / user_id
            images_dir = base_dir / settings.IMAGES_DIRECTORY
        else:
            images_dir = Path(settings.IMAGES_DIRECTORY)

        images_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectory for processed images only
        if settings.SAVE_PROCESSED:
            (images_dir / "processed").mkdir(exist_ok=True)

        return images_dir

    @staticmethod
    def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
        """
        Generate a unique filename to prevent conflicts

        Args:
            original_filename: Original uploaded filename
            prefix: Optional prefix for the filename

        Returns:
            Unique filename with timestamp and UUID
        """
        # Get file extension
        file_path = Path(original_filename)
        extension = file_path.suffix.lower()
        name_without_ext = file_path.stem

        # Generate timestamp and unique ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        # Construct unique filename
        if prefix:
            unique_filename = (
                f"{timestamp}_{prefix}_{name_without_ext}_{unique_id}{extension}"
            )
        else:
            unique_filename = f"{timestamp}_{name_without_ext}_{unique_id}{extension}"

        return unique_filename

    @staticmethod
    def save_processed_image(
        image: Image.Image, unique_filename: str, user_id: str = None
    ) -> str:
        """
        Save processed image using the unified image storage service.
        
        Args:
            image: PIL Image object to save
            unique_filename: Unique filename for the image
            user_id: User ID for organizing images
            
        Returns:
            Storage path/URL if successful, None otherwise
        """
        image_storage = get_image_storage_service()
        return image_storage.save_processed_image(image, unique_filename, user_id)

    @staticmethod
    def get_user_json_file_path(user_id: str) -> Path:
        """
        Get the path to the user-specific JSON file

        Args:
            user_id: User identifier

        Returns:
            Path to the user's JSON file
        """
        # Normalize and validate user_id
        user_id = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
        if settings.CREATE_USER_SUBDIRS:
            user_dir = Path(settings.USER_DATA_DIRECTORY) / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir / settings.ATTRIBUTES_JSON_FILE
        else:
            # Fallback to user-prefixed filename in root directory
            filename = f"{user_id}_{settings.ATTRIBUTES_JSON_FILE}"
            return Path(filename)

    @staticmethod
    def calculate_image_hash(image_data: bytes) -> str:
        """
        Calculate SHA-256 hash of image data for duplicate detection

        Args:
            image_data: Raw image bytes

        Returns:
            SHA-256 hash string
        """
        return hashlib.sha256(image_data).hexdigest()

    @staticmethod
    def load_existing_attributes(user_id: str) -> Dict[str, Any]:
        logger = get_logger(__name__)
        user_id_norm = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
        data_service = get_data_service()
        user_data = data_service.load_user_data(user_id_norm)
        if user_data:
            logger.debug(f"[user={user_id}] Loaded existing attributes from data service.")
            return user_data
        logger.info(f"[user={user_id}] No existing attributes found, initializing new record.")
        return {
            "images": {},
            "metadata": {"total_images": 0, "last_updated": None, "user_id": user_id},
        }

    @staticmethod
    def save_attributes_to_json(
        image_hash: str,
        attributes: Dict[str, Any],
        image_info: ImageInfo,
        user_id: str,
        saved_paths: Dict[str, str] = None,
    ):
        logger = get_logger(__name__)
        if not settings.SAVE_ATTRIBUTES_JSON:
            logger.info(f"[user={user_id}] Skipping attribute save (SAVE_ATTRIBUTES_JSON is False)")
            return
        user_id_norm = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
        data = ClothingAttributionService.load_existing_attributes(user_id_norm)
        entry = {
            "filename": image_info.filename,
            "content_type": image_info.content_type,
            "file_size_bytes": image_info.file_size_bytes,
            "file_size_mb": image_info.file_size_mb,
            "attributes": attributes,
            "processed_timestamp": datetime.now().isoformat(),
            "image_hash": image_hash,
            "user_id": user_id,
        }
        if saved_paths:
            entry["saved_images"] = saved_paths
        data["images"][image_hash] = entry
        data["metadata"]["total_images"] = len(data["images"])
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        data["metadata"]["user_id"] = user_id
        data_service = get_data_service()
        success = data_service.save_user_data(user_id_norm, data)
        if success:
            logger.info(f"[user={user_id}] Attributes saved for image {image_info.filename} (hash={image_hash})")
        else:
            logger.error(f"[user={user_id}] Failed to save attributes for image {image_info.filename} (hash={image_hash})")

    @staticmethod
    def is_duplicate_image(
        image_hash: str, user_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        logger = get_logger(__name__)
        user_id_norm = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
        if not settings.AVOID_DUPLICATES:
            logger.debug(f"[user={user_id}] Duplicate check skipped (AVOID_DUPLICATES is False)")
            return False, {}
        existing_data = ClothingAttributionService.load_existing_attributes(user_id_norm)
        if image_hash in existing_data.get("images", {}):
            logger.info(f"[user={user_id}] Duplicate image detected (hash={image_hash})")
            return True, existing_data["images"][image_hash]
        logger.debug(f"[user={user_id}] Image is unique (hash={image_hash})")
        return False, {}

    @staticmethod
    async def process_images_for_attributes(
        files: List[UploadFile],
        user_id: str,
    ) -> AttributeAnalysisResponse:
        logger = get_logger(__name__)
        logger.info(f"[user={user_id}] 📸 Starting batch attribute analysis | {len(files)} files | Storage: {'GCS' if settings.USE_GCS else 'Local'}")
        
        if not files:
            logger.warning(f"[user={user_id}] No files provided for attribute analysis")
            raise HTTPException(status_code=400, detail="No files provided")

        if not user_id or not user_id.strip():
            logger.error("User ID is missing or empty for attribute analysis")
            raise HTTPException(status_code=400, detail="User ID is required")

        # Normalize and validate user_id
        user_id_norm = normalize_user_id(user_id, base_dir=settings.USER_DATA_DIRECTORY)
        logger.debug(f"[user={user_id}] Normalized user ID: {user_id_norm}")

        # Limit the number of files to prevent abuse
        max_files = 10  # You can make this configurable
        if len(files) > max_files:
            logger.warning(f"[user={user_id}] Too many files provided ({len(files)} > {max_files})")
            raise HTTPException(
                status_code=400, detail=f"Too many files. Maximum allowed: {max_files}"
            )

        # Log file summary
        file_names = [f.filename for f in files]
        logger.info(f"[user={user_id}] Files to process: {', '.join(file_names)}")

        results = []
        successful_analyses = 0
        failed_analyses = 0

        # Process each image
        for i, file in enumerate(files, 1):
            try:
                logger.info(f"[user={user_id}] 🔄 Processing image {i}/{len(files)}: {file.filename}")
                result = await ClothingAttributionService.process_single_image_analysis(
                    file, user_id
                )
                results.append(result)
                
                if result.error is None:
                    successful_analyses += 1
                    category = result.attributes.get('category', 'Unknown') if result.attributes else 'Unknown'
                    status_emoji = "✅" if result.status == "attributes_extracted" else "🔄"
                    logger.info(f"[user={user_id}] {status_emoji} Success {i}/{len(files)}: {file.filename} | Category: {category}")
                else:
                    failed_analyses += 1
                    logger.warning(f"[user={user_id}] ❌ Failed {i}/{len(files)}: {file.filename} | Error: {result.error}")
            except Exception as e:
                # Create error result for this image
                try:
                    file_size = await ClothingAttributionService.validate_file_size(
                        file
                    )
                    image_info = ClothingAttributionService.create_image_info(
                        file, file_size
                    )
                except:
                    # If we can't even get file info, create a minimal one
                    image_info = ImageInfo(
                        filename=file.filename or "unknown",
                        content_type=file.content_type or "unknown",
                        file_size_bytes=0,
                        file_size_mb=0.0,
                    )

                error_result = ImageAnalysisResult(
                    image_info=image_info, status="error", attributes=None, error=str(e)
                )
                results.append(error_result)
                failed_analyses += 1
                logger.error(f"[user={user_id}] ❌ Exception during processing {i}/{len(files)}: {file.filename} | Error: {e}")
        # Determine overall success
        overall_success = successful_analyses > 0

        if successful_analyses == len(files):
            message = f"All {len(files)} images processed successfully for user {user_id}"
            logger.info(f"[user={user_id}] 🎉 {message}")
        elif successful_analyses > 0:
            message = f"{successful_analyses} of {len(files)} images processed successfully for user {user_id}"
            logger.warning(f"[user={user_id}] ⚠️ Partial success: {message}")
        else:
            message = f"Failed to process all {len(files)} images for user {user_id}"
            logger.error(f"[user={user_id}] 💥 {message}")

        logger.info(f"[user={user_id}] 📊 Batch analysis complete | Success: {successful_analyses}, Failed: {failed_analyses}, Total: {len(files)}")
        return AttributeAnalysisResponse(
            success=overall_success,
            message=message,
            processing_timestamp=datetime.now().isoformat(),
            total_images=len(files),
            successful_analyses=successful_analyses,
            failed_analyses=failed_analyses,
            results=results,
        )

    @staticmethod
    async def process_single_image_analysis(
        file: UploadFile, user_id: str
    ) -> ImageAnalysisResult:
        logger = get_logger(__name__)
        logger.info(f"[user={user_id}] Starting image analysis for: {file.filename}")
        saved_paths = {}
        try:
            # Validate file type
            if not ClothingAttributionService.validate_image_file(file):
                logger.warning(f"[user={user_id}] Invalid file type for: {file.filename} | Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}")
                raise ValueError(
                    f"Invalid file type. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                )

            # Validate file size
            file_size = await ClothingAttributionService.validate_file_size(file)
            logger.debug(f"[user={user_id}] File size validated: {file_size} bytes for {file.filename}")

            # Create image info
            image_info = ClothingAttributionService.create_image_info(file, file_size)

            # Load and calculate hash for duplicate detection
            image_data = await file.read()
            image_hash = ClothingAttributionService.calculate_image_hash(image_data)
            logger.debug(f"[user={user_id}] Generated image hash: {image_hash[:8]}... for {file.filename}")

            # Check for duplicates for this specific user
            is_duplicate, existing_data = ClothingAttributionService.is_duplicate_image(
                image_hash, user_id
            )

            if is_duplicate:
                logger.info(f"[user={user_id}] Duplicate image detected: {file.filename} (hash: {image_hash[:8]}...)")
                
                # Get download URL for existing duplicate image
                duplicate_download_url = None
                if existing_data.get("saved_images", {}).get("processed"):
                    from app.core.image_storage_service import get_image_storage_service
                    image_storage = get_image_storage_service()
                    duplicate_download_url = image_storage.get_download_url(
                        existing_data["saved_images"]["processed"]
                    )
                    logger.debug(f"[user={user_id}] Retrieved download URL for duplicate image")
                
                return ImageAnalysisResult(
                    image_info=image_info,
                    status="duplicate_found",
                    attributes={
                        **existing_data.get("attributes", {}),
                        "duplicate_info": {
                            "original_filename": existing_data.get("filename"),
                            "original_processed_timestamp": existing_data.get(
                                "processed_timestamp"
                            ),
                            "is_duplicate": True,
                            "user_id": user_id,
                        },
                    },
                    error=None,
                    image_url=duplicate_download_url,
                )

            logger.debug(f"[user={user_id}] Opening image for processing: {file.filename}")
            pil_image = Image.open(io.BytesIO(image_data))

            unique_filename = ClothingAttributionService.generate_unique_filename(
                file.filename, user_id
            )
            logger.debug(f"[user={user_id}] Generated unique filename: {unique_filename}")

            logger.debug(f"[user={user_id}] Starting image compression and resizing for: {file.filename}")
            processed_image, processing_info = (
                ClothingAttributionService.compress_and_resize_image(pil_image)
            )
            logger.debug(f"[user={user_id}] Image processed - Original: {processing_info.get('original_size')}, Final: {processing_info.get('processed_size')}")

            if settings.SAVE_IMAGES and settings.SAVE_PROCESSED:
                logger.debug(f"[user={user_id}] Saving processed image: {unique_filename}")
                processed_path = ClothingAttributionService.save_processed_image(
                    processed_image, unique_filename, user_id
                )
                saved_paths["processed"] = processed_path
                
                # Log storage type and path
                if processed_path:
                    storage_type = "GCS" if processed_path.startswith("gs://") else "Local"
                    logger.info(f"[user={user_id}] Processed image saved to {storage_type}: {processed_path}")
                else:
                    logger.warning(f"[user={user_id}] Failed to save processed image")

            # Extract clothing attributes using Gemini (async to avoid blocking event loop)
            logger.info(f"[user={user_id}] Starting AI attribute extraction for: {file.filename}")
            attributes = await ClothingAttributionService.extract_clothing_attributes(
                processed_image, file.filename
            )

            # Hardened error handling for Gemini extraction
            if not isinstance(attributes, dict) or "error" in attributes:
                await file.seek(0)
                error_message = (
                    attributes["error"]
                    if isinstance(attributes, dict) and "error" in attributes
                    else f"Invalid Gemini response format: expected dict, got {type(attributes).__name__}"
                )
                logger.error(f"[user={user_id}] Attribute extraction failed for {file.filename}: {error_message}")
                return ImageAnalysisResult(
                    image_info=image_info,
                    status="attributes_failed",
                    attributes=None,
                    error=error_message,
                )

            if saved_paths:
                attributes["saved_images"] = saved_paths

            attributes["processing_info"] = processing_info
            attributes["image_hash"] = image_hash
            attributes["user_id"] = user_id

            # Only persist attributes if Gemini extraction succeeded
            logger.debug(f"[user={user_id}] Saving attributes to data store for: {file.filename}")
            ClothingAttributionService.save_attributes_to_json(
                image_hash, attributes, image_info, user_id, saved_paths
            )

            # Get download URL for the processed image
            download_url = None
            if saved_paths.get("processed"):
                from app.core.image_storage_service import get_image_storage_service
                image_storage = get_image_storage_service()
                download_url = image_storage.get_download_url(saved_paths["processed"])
                
                if download_url:
                    url_type = "Signed URL" if "https://" in download_url else "Local Path"
                    logger.info(f"[user={user_id}] Generated {url_type} for processed image: {file.filename}")
                else:
                    logger.warning(f"[user={user_id}] Failed to generate download URL for: {file.filename}")

            await file.seek(0)
            logger.info(f"[user={user_id}] ✅ Image analysis completed successfully: {file.filename} | Category: {attributes.get('category', 'Unknown')}")
            return ImageAnalysisResult(
                image_info=image_info,
                status="attributes_extracted",
                attributes=attributes,
                error=None,
                image_url=download_url,
            )
        except Exception as e:
            try:
                if file.filename:
                    file_size = await ClothingAttributionService.validate_file_size(
                        file
                    )
                    image_info = ClothingAttributionService.create_image_info(
                        file, file_size
                    )
                else:
                    raise ValueError("No filename")
            except:
                image_info = ImageInfo(
                    filename=file.filename or "unknown",
                    content_type=file.content_type or "unknown",
                    file_size_bytes=0,
                    file_size_mb=0.0,
                )
            logger.error(f"Exception in single image analysis: {file.filename} | {e}")
            return ImageAnalysisResult(
                image_info=image_info, status="error", attributes=None, error=str(e)
            )
        finally:
            try:
                await file.close()
            except:
                pass

    @staticmethod
    async def extract_clothing_attributes(
        image: Image.Image, image_filename: str = None
    ) -> Dict[str, Any]:
        logger = get_logger(__name__)
        logger.debug(f"🧠 Starting AI attribute extraction | Image: {image_filename} | Size: {image.size}")
        
        try:
            # Initialize Gemini attributor
            gemini_attributor = GeminiAttributor()

            # Use asyncio.to_thread to run the blocking Gemini extraction in a thread
            # This prevents blocking the FastAPI event loop
            attributes = await asyncio.to_thread(
                gemini_attributor.extract, image, image_filename
            )

            # Add processing metadata
            width, height = image.size
            attributes["processing_metadata"] = {
                "processed_image_dimensions": f"{width}x{height}",
                "extraction_method": "gemini_ai",
                "model": "gemini-2.0-flash",
            }

            logger.info(f"✅ AI attribute extraction successful | Image: {image_filename} | Category: {attributes.get('category', 'Unknown')}")
            return attributes

        except Exception as e:
            logger.error(f"❌ AI attribute extraction failed | Image: {image_filename} | Error: {e}")
            return {
                "error": f"Failed to extract attributes using Gemini: {str(e)}",
                "fallback_data": {
                    "clothing_type": "unknown",
                    "category": "unknown",
                    "primary_color": "unknown",
                    "extraction_method": "failed_gemini",
                    "image_dimensions": f"{image.size[0]}x{image.size[1]}",
                },
            }

    @staticmethod
    def get_compressed_image_bytes(image: Image.Image, format: str = "JPEG") -> bytes:
        """
        Convert processed PIL image back to bytes for further processing

        Args:
            image: Processed PIL Image object
            format: Output format ('JPEG', 'PNG', etc.)

        Returns:
            Image bytes with applied compression
        """
        img_byte_arr = io.BytesIO()

        # Save with optimal settings for clothing recognition
        if format.upper() == "JPEG":
            image.save(
                img_byte_arr,
                format=format,
                quality=settings.JPEG_QUALITY,
                optimize=True,
            )
        else:
            image.save(img_byte_arr, format=format, optimize=True)

        return img_byte_arr.getvalue()
