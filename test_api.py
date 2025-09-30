#!/usr/bin/env python3
"""
Test script for the Fashion Backend API
"""

import requests
import json
from pathlib import Path
import tempfile
from PIL import Image


def create_test_image(color="red", size=(100, 100)):
    """Create a simple test image with specified color"""
    img = Image.new("RGB", size, color=color)

    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(temp_file.name, "JPEG")
    return temp_file.name


def test_api():
    """Test the FastAPI endpoints"""
    base_url = "http://localhost:8000"

    print("Testing Fashion Backend API")
    print("=" * 40)

    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print(
            "❌ Cannot connect to API. Make sure the server is running at http://localhost:8000"
        )
        return

    # Test root endpoint
    print("\n2. Testing root endpoint...")
    response = requests.get(f"{base_url}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test image processing endpoint
    print("\n3. Testing image processing endpoint...")
    test_image_paths = [
        create_test_image("red", (150, 150)),
        create_test_image("blue", (200, 100)),
        create_test_image("green", (100, 200)),
    ]

    try:
        files = []
        file_objects = []

        # Open all files
        for i, path in enumerate(test_image_paths):
            f = open(path, "rb")
            file_objects.append(f)
            files.append(("files", (f"test_image_{i+1}.jpg", f, "image/jpeg")))

        response = requests.post(f"{base_url}/api/v1/attribute_clothes", files=files)

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Images processed successfully!")
            result = response.json()
            print(f"Total images: {result.get('total_images', 0)}")
            print(f"Successful analyses: {result.get('successful_analyses', 0)}")
            print(f"Failed analyses: {result.get('failed_analyses', 0)}")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Image processing failed: {response.text}")

    except Exception as e:
        print(f"❌ Error during image processing: {e}")

    finally:
        # Close all file objects
        for f in file_objects:
            f.close()
        # Clean up test images
        for path in test_image_paths:
            Path(path).unlink(missing_ok=True)

    print("\n" + "=" * 40)
    print("Testing complete!")


if __name__ == "__main__":
    test_api()
