#!/usr/bin/env python3
"""
Test script for image compression functionality
"""

from app.services.image_service import ImageProcessingService
from PIL import Image
import io


def test_image_compression():
    """Test the image compression and resizing functionality"""
    print("Testing Image Compression Functionality")
    print("=" * 45)

    # Create test images with different sizes
    test_cases = [
        (2000, 1500, "Large landscape image"),
        (1000, 2000, "Large portrait image"),
        (800, 800, "Square image"),
        (300, 400, "Small image"),
    ]

    for width, height, description in test_cases:
        print(f"\n{description} ({width}x{height}):")

        # Create test image
        test_image = Image.new("RGB", (width, height), color="blue")

        # Compress and resize
        processed_image, processing_info = (
            ImageProcessingService.compress_and_resize_image(test_image)
        )

        print(f"  Original size: {processing_info['original_size']}")
        print(f"  Processed size: {processing_info['processed_size']}")
        print(f"  Scale factor: {processing_info['scale_factor']}")
        print(f"  Size reduction ratio: {processing_info['size_reduction_ratio']}")

        # Test converting back to bytes
        image_bytes = ImageProcessingService.get_compressed_image_bytes(processed_image)
        print(f"  Compressed size: {len(image_bytes) / 1024:.1f} KB")


if __name__ == "__main__":
    test_image_compression()
