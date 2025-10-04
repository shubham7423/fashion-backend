#!/usr/bin/env python3
"""
Test script for the Styler API endpoint
"""

import pytest
import requests
import json
from pathlib import Path

TIMEOUT = 10  # seconds for all HTTP requests


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.slow
def test_styler_api():
    """Test the Styler endpoint"""
    base_url = "http://localhost:8000"

    print("Testing Fashion Backend Styler API")
    print("=" * 50)

    # Test parameters
    test_user_id = "shubham"  # User who has uploaded images
    test_city = "New York"
    test_weather = (
        "cool autumn weather - expect temperatures around 12-18°C, light rain expected"
    )
    test_occasion = "business casual meeting"

    print(f"\n🧥 Testing outfit recommendation for:")
    print(f"   User: {test_user_id}")
    print(f"   City: {test_city}")
    print(f"   Weather: {test_weather}")
    print(f"   Occasion: {test_occasion}")

    # Test styler endpoint
    print(f"\n📡 Calling styler endpoint...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/styler",
            params={
                "user_id": test_user_id,
                "city": test_city,
                "weather": test_weather,
                "occasion": test_occasion,
            },
            timeout=TIMEOUT,
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Styler API working successfully!")
            print(f"\n📊 Summary:")
            print(f"   Success: {result.get('success', False)}")
            print(f"   User ID: {result.get('user_id', 'N/A')}")
            print(f"   Available Items: {result.get('available_items_count', 0)}")
            print(f"   Message: {result.get('message', 'N/A')}")

            outfit = result.get("outfit_recommendation")
            if outfit and not outfit.get("error"):
                print(f"\n👔 Outfit Recommendation:")
                print(f"   Top: {outfit.get('top', 'N/A')}")
                print(f"   Bottom: {outfit.get('bottom', 'N/A')}")
                print(f"   Outerwear: {outfit.get('outerwear', 'N/A')}")
                print(f"   Justification: {outfit.get('justification', 'N/A')}")
                print(f"   Style Notes: {outfit.get('style_notes', 'N/A')}")
                print(
                    f"   Weather Consideration: {outfit.get('weather_consideration', 'N/A')}"
                )
                print(f"   Accessories: {outfit.get('other_accessories', 'N/A')}")
            elif outfit and outfit.get("error"):
                print(f"❌ Outfit generation error: {outfit.get('error')}")
            else:
                print("⚠️  No outfit recommendation generated")

        elif response.status_code == 404:
            print("❌ User not found or no clothing data available")
            print("💡 Tip: Upload some images first using /attribute_clothes endpoint")
        else:
            print(f"❌ Request failed: {response.status_code}")
            try:
                error_info = response.json()
                print(f"   Error: {error_info.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print(
            "❌ Cannot connect to API. Make sure the server is running at http://localhost:8000"
        )
        return
    except Exception as e:
        print(f"❌ Error during styler test: {e}")

    # Test with default parameters
    print(f"\n🔄 Testing with default parameters...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/styler", params={"user_id": test_user_id}, timeout=TIMEOUT
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Default parameters test successful!")
            print(f"   Available Items: {result.get('available_items_count', 0)}")
        else:
            print(f"❌ Default parameters test failed")

    except Exception as e:
        print(f"❌ Error during default parameters test: {e}")

    print("\n" + "=" * 50)
    print("Styler API testing complete!")


@pytest.mark.integration
@pytest.mark.api
def test_health_endpoint():
    """Quick health check"""
    base_url = "http://localhost:8000"
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print("✅ API is healthy and running")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except:
        print("❌ Cannot connect to API")
        return False


if __name__ == "__main__":
    print("🏃 Starting API tests...\n")

    # Check if API is running
    if test_health_endpoint():
        test_styler_api()
    else:
        print("\n💡 Please start the API server first:")
        print("   python main.py")
