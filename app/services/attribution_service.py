from fastapi import UploadFile, HTTPException
from pathlib import Path
from app.core.config import settings
from app.models.response import ImageInfo, AttributeAnalysisResponse
from datetime import datetime
from typing import Any, Dict, Tuple
import io
from PIL import Image, ImageOps


class ImageProcessingService:
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
    async def process_image_for_attributes(
        file: UploadFile,
    ) -> AttributeAnalysisResponse:
        """
        Process image for clothing attribute analysis

        This method receives the image file and prepares it for processing.
        Currently returns basic file information. In the future, this is where
        you would add your ML model or image processing logic.
        """
        try:
            # Validate file type
            if not ImageProcessingService.validate_image_file(file):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
                )

            # Validate file size
            file_size = await ImageProcessingService.validate_file_size(file)

            # Create image info
            image_info = ImageProcessingService.create_image_info(file, file_size)

            # Here you can add your image processing logic
            # For example:
            # - Load the image using PIL
            # - Run it through your ML model
            # - Extract clothing attributes
            # - Return the analysis results

            # Example of loading the image (for future processing)
            image_data = await file.read()

            # Load and process the image
            try:
                pil_image = Image.open(io.BytesIO(image_data))

                # Compress and resize the image for optimal clothing recognition
                processed_image, processing_info = (
                    ImageProcessingService.compress_and_resize_image(pil_image)
                )

                # Here you can add your ML model processing
                # The processed_image is now optimized for clothing recognition
                # attributes = your_ml_model.analyze(processed_image)

                # Example: Save processed image info for debugging (optional)
                print(f"Image processed: {processing_info}")

            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid image format: {str(e)}"
                )

            # Reset file pointer if needed for further processing
            await file.seek(0)

            # Return response with placeholder for attributes
            return AttributeAnalysisResponse(
                success=True,
                message="Image processed, compressed, and ready for attribute analysis",
                image_info=image_info,
                processing_timestamp=datetime.now().isoformat(),
                status="processed_and_ready",
                attributes=None,  # This will contain your ML model results
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error processing image: {str(e)}"
            )
        finally:
            await file.close()

    @staticmethod
    def extract_clothing_attributes(image: Image.Image) -> Dict[str, Any]:
        """
        Extract clothing attributes from the processed image

        This is a placeholder method where you would implement your
        machine learning model or image processing logic.

        Args:
            image: PIL Image object (already processed and compressed)

        Returns:
            Dictionary containing extracted attributes
        """
        # Placeholder implementation
        # In a real implementation, you would:
        # 1. The image is already preprocessed and optimized
        # 2. Run it through your trained model
        # 3. Post-process the results
        # 4. Return structured attribute data

        # Get image dimensions for reference
        width, height = image.size

        return {
            "clothing_type": "placeholder",
            "colors": ["placeholder"],
            "patterns": ["placeholder"],
            "style": "placeholder",
            "material": "placeholder",
            "texture": "placeholder",
            "image_dimensions": f"{width}x{height}",
            "confidence_scores": {
                "clothing_type": 0.0,
                "colors": 0.0,
                "patterns": 0.0,
                "style": 0.0,
                "material": 0.0,
                "texture": 0.0,
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
