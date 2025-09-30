#!/usr/bin/env python3
"""
Test script for the Fashion Backend API
"""

import requests
import json
from pathlib import Path
import tempfile
from PIL import Image


def create_test_image():
    """Create a simple test image"""
    # Create a simple red square image
    img = Image.new("RGB", (100, 100), color="red")

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
    test_image_path = create_test_image()

    try:
        with open(test_image_path, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            response = requests.post(
                f"{base_url}/api/v1/attribute_clothes", files=files
            )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Image processed successfully!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Processing failed: {response.text}")

    except Exception as e:
        print(f"❌ Error during processing: {e}")

    finally:
        # Clean up test image
        Path(test_image_path).unlink(missing_ok=True)

    print("\n" + "=" * 40)
    print("Testing complete!")


if __name__ == "__main__":
    test_api()
