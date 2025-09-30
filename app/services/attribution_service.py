from fastapi import UploadFile, HTTPException
from pathlib import Path
from app.core.config import settings
from app.models.response import ImageInfo, AttributeAnalysisResponse, ImageAnalysisResult
from app.services.attribution.gemini_attributor import GeminiAttributor
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
        if user_id and settings.CREATE_USER_SUBDIRS:
            # Create user-specific directory structure
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
            unique_filename = f"{timestamp}_{prefix}_{name_without_ext}_{unique_id}{extension}"
        else:
            unique_filename = f"{timestamp}_{name_without_ext}_{unique_id}{extension}"
            
        return unique_filename

    @staticmethod
    def save_processed_image(image: Image.Image, unique_filename: str, user_id: str = None) -> str:
        """
        Save the processed/compressed image
        
        Args:
            image: Processed PIL Image object
            unique_filename: Unique filename to save with
            user_id: Optional user ID for user-specific storage
            
        Returns:
            Path where the processed image was saved
        """
        if not settings.SAVE_IMAGES or not settings.SAVE_PROCESSED:
            return None
            
        images_dir = ClothingAttributionService.ensure_images_directory(user_id)
        processed_dir = images_dir / "processed"
        
        # Change extension to .jpg for processed images (since we compress them)
        file_path = Path(unique_filename)
        processed_filename = f"{file_path.stem}_processed.jpg"
        file_path = processed_dir / processed_filename
        
        # Save the processed image with optimal settings
        image.save(
            file_path,
            format="JPEG",
            quality=settings.JPEG_QUALITY,
            optimize=True
        )
        
        return str(file_path)

    @staticmethod
    def get_user_json_file_path(user_id: str) -> Path:
        """
        Get the path to the user-specific JSON file
        
        Args:
            user_id: User identifier
            
        Returns:
            Path to the user's JSON file
        """
        if settings.CREATE_USER_SUBDIRS:
            user_dir = Path(settings.USER_DATA_DIRECTORY) / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir / settings.ATTRIBUTES_JSON_FILE
        else:
            # Fallback to user-prefixed filename in root directory
            filename = f"{user_id}_{settings.ATTRIBUTES_JSON_FILE}"
            return Path(filename)
        """
        Calculate SHA-256 hash of image data for duplicate detection
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            SHA-256 hash string
        """
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
        """
        Load existing attributes from user-specific JSON file
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary containing existing attributes or empty dict if file doesn't exist
        """
        json_file_path = ClothingAttributionService.get_user_json_file_path(user_id)
        
        if json_file_path.exists():
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted or unreadable, return empty structure
                return {"images": {}, "metadata": {"total_images": 0, "last_updated": None, "user_id": user_id}}
        
        return {"images": {}, "metadata": {"total_images": 0, "last_updated": None, "user_id": user_id}}

    @staticmethod
    def save_attributes_to_json(image_hash: str, attributes: Dict[str, Any], image_info: ImageInfo, user_id: str, saved_paths: Dict[str, str] = None):
        """
        Save image attributes to user-specific JSON file
        
        Args:
            image_hash: Unique hash of the image
            attributes: Extracted attributes from the image
            image_info: Image metadata
            user_id: User identifier
            saved_paths: Dictionary of saved file paths
        """
        if not settings.SAVE_ATTRIBUTES_JSON:
            return
            
        # Load existing data for this user
        data = ClothingAttributionService.load_existing_attributes(user_id)
        
        # Create new entry
        entry = {
            "filename": image_info.filename,
            "content_type": image_info.content_type,
            "file_size_bytes": image_info.file_size_bytes,
            "file_size_mb": image_info.file_size_mb,
            "attributes": attributes,
            "processed_timestamp": datetime.now().isoformat(),
            "image_hash": image_hash,
            "user_id": user_id
        }
        
        # Add saved paths if available
        if saved_paths:
            entry["saved_paths"] = saved_paths
            
        # Add to images dictionary using hash as key
        data["images"][image_hash] = entry
        
        # Update metadata
        data["metadata"]["total_images"] = len(data["images"])
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        data["metadata"]["user_id"] = user_id
        
        # Save back to user-specific file
        json_file_path = ClothingAttributionService.get_user_json_file_path(user_id)
        try:
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save attributes to JSON file for user {user_id}: {e}")

    @staticmethod
    def is_duplicate_image(image_hash: str, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if image is a duplicate based on its hash for a specific user
        
        Args:
            image_hash: SHA-256 hash of the image
            user_id: User identifier
            
        Returns:
            Tuple of (is_duplicate, existing_data)
        """
        if not settings.AVOID_DUPLICATES:
            return False, {}
            
        existing_data = ClothingAttributionService.load_existing_attributes(user_id)
        
        if image_hash in existing_data.get("images", {}):
            return True, existing_data["images"][image_hash]
        
        return False, {}

    @staticmethod
    async def process_images_for_attributes(
        files: List[UploadFile],
        user_id: str,
    ) -> AttributeAnalysisResponse:
        """
        Process images for clothing attribute analysis for a specific user
        
        This method processes image files and returns analysis results for all images.
        
        Args:
            files: List of image files to be processed
            user_id: User identifier for user-specific storage
            
        Returns:
            AttributeAnalysisResponse with results for all images
        """
        if not files:
            raise HTTPException(
                status_code=400,
                detail="No files provided"
            )
        
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="User ID is required"
            )
        
        # Sanitize user_id to prevent directory traversal attacks
        user_id = user_id.strip().replace("/", "_").replace("\\", "_").replace("..", "_")
        
        # Limit the number of files to prevent abuse
        max_files = 10  # You can make this configurable
        if len(files) > max_files:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Maximum allowed: {max_files}"
            )
        
        results = []
        successful_analyses = 0
        failed_analyses = 0
        
        # Process each image
        for file in files:
            try:
                result = await ClothingAttributionService.process_single_image_analysis(file, user_id)
                results.append(result)
                if result.error is None:
                    successful_analyses += 1
                else:
                    failed_analyses += 1
            except Exception as e:
                # Create error result for this image
                try:
                    file_size = await ClothingAttributionService.validate_file_size(file)
                    image_info = ClothingAttributionService.create_image_info(file, file_size)
                except:
                    # If we can't even get file info, create a minimal one
                    image_info = ImageInfo(
                        filename=file.filename or "unknown",
                        content_type=file.content_type or "unknown",
                        file_size_bytes=0,
                        file_size_mb=0.0
                    )
                
                error_result = ImageAnalysisResult(
                    image_info=image_info,
                    status="error",
                    attributes=None,
                    error=str(e)
                )
                results.append(error_result)
                failed_analyses += 1
        
        # Determine overall success
        overall_success = successful_analyses > 0
        
        if successful_analyses == len(files):
            message = f"All {len(files)} images processed successfully for user {user_id}"
        elif successful_analyses > 0:
            message = f"{successful_analyses} of {len(files)} images processed successfully for user {user_id}"
        else:
            message = f"Failed to process all {len(files)} images for user {user_id}"
        
        return AttributeAnalysisResponse(
            success=overall_success,
            message=message,
            processing_timestamp=datetime.now().isoformat(),
            total_images=len(files),
            successful_analyses=successful_analyses,
            failed_analyses=failed_analyses,
            results=results
        )

    @staticmethod
    async def process_single_image_analysis(file: UploadFile, user_id: str) -> ImageAnalysisResult:
        """
        Process a single image and return ImageAnalysisResult for a specific user
        
        Args:
            file: Image file to process
            user_id: User identifier for user-specific storage
            
        Returns:
            ImageAnalysisResult with analysis data or error
        """
        saved_paths = {}
        
        try:
            # Validate file type
            if not ClothingAttributionService.validate_image_file(file):
                raise ValueError(f"Invalid file type. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}")

            # Validate file size
            file_size = await ClothingAttributionService.validate_file_size(file)

            # Create image info
            image_info = ClothingAttributionService.create_image_info(file, file_size)

            # Load and calculate hash for duplicate detection
            image_data = await file.read()
            image_hash = ClothingAttributionService.calculate_image_hash(image_data)

            # Check for duplicates for this specific user
            is_duplicate, existing_data = ClothingAttributionService.is_duplicate_image(image_hash, user_id)
            
            if is_duplicate:
                # Return existing attributes for duplicate image
                return ImageAnalysisResult(
                    image_info=image_info,
                    status="duplicate_found",
                    attributes={
                        **existing_data.get("attributes", {}),
                        "duplicate_info": {
                            "original_filename": existing_data.get("filename"),
                            "original_processed_timestamp": existing_data.get("processed_timestamp"),
                            "is_duplicate": True,
                            "user_id": user_id
                        }
                    },
                    error=None
                )

            # Process new image
            pil_image = Image.open(io.BytesIO(image_data))

            # Generate unique filename for saving
            unique_filename = ClothingAttributionService.generate_unique_filename(file.filename, user_id)

            # Compress and resize the image for optimal clothing recognition
            processed_image, processing_info = (
                ClothingAttributionService.compress_and_resize_image(pil_image)
            )

            # Save processed image if enabled (user-specific)
            if settings.SAVE_IMAGES and settings.SAVE_PROCESSED:
                processed_path = ClothingAttributionService.save_processed_image(processed_image, unique_filename, user_id)
                saved_paths["processed"] = processed_path

            # Extract clothing attributes using Gemini
            attributes = ClothingAttributionService.extract_clothing_attributes(
                processed_image, file.filename
            )

            # Add saved paths to attributes if images were saved
            if saved_paths:
                attributes["saved_images"] = saved_paths

            # Add processing information
            attributes["processing_info"] = processing_info
            attributes["image_hash"] = image_hash
            attributes["user_id"] = user_id

            # Save attributes to user-specific JSON file for first-time images
            ClothingAttributionService.save_attributes_to_json(
                image_hash, attributes, image_info, user_id, saved_paths
            )

            # Reset file pointer
            await file.seek(0)

            return ImageAnalysisResult(
                image_info=image_info,
                status="attributes_extracted",
                attributes=attributes,
                error=None
            )

        except Exception as e:
            # Try to get image info for error case
            try:
                if file.filename:
                    file_size = await ClothingAttributionService.validate_file_size(file)
                    image_info = ClothingAttributionService.create_image_info(file, file_size)
                else:
                    raise ValueError("No filename")
            except:
                # Create minimal image info for error case
                image_info = ImageInfo(
                    filename=file.filename or "unknown",
                    content_type=file.content_type or "unknown",
                    file_size_bytes=0,
                    file_size_mb=0.0
                )

            return ImageAnalysisResult(
                image_info=image_info,
                status="error",
                attributes=None,
                error=str(e)
            )
        finally:
            try:
                await file.close()
            except:
                pass

    @staticmethod
    def extract_clothing_attributes(image: Image.Image, image_filename: str = None) -> Dict[str, Any]:
        """
        Extract clothing attributes from the processed image using Gemini AI

        Args:
            image: PIL Image object (already processed and compressed)
            image_filename: Optional filename for context

        Returns:
            Dictionary containing extracted attributes from Gemini
        """
        try:
            # Initialize Gemini attributor
            gemini_attributor = GeminiAttributor()
            
            # Use Gemini to extract clothing attributes
            attributes = gemini_attributor.extract(image, image_filename)
            
            # Add processing metadata
            width, height = image.size
            attributes["processing_metadata"] = {
                "processed_image_dimensions": f"{width}x{height}",
                "extraction_method": "gemini_ai",
                "model": "gemini-2.0-flash"
            }
            
            return attributes
            
        except Exception as e:
            # Return error information if Gemini processing fails
            return {
                "error": f"Failed to extract attributes using Gemini: {str(e)}",
                "fallback_data": {
                    "clothing_type": "unknown",
                    "category": "unknown", 
                    "primary_color": "unknown",
                    "extraction_method": "failed_gemini",
                    "image_dimensions": f"{image.size[0]}x{image.size[1]}"
                }
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
