#!/usr/bin/env python3
"""
Comprehensive test script for multimodal integration
Tests the complete workflow from image upload to answer generation
"""

import asyncio
import base64
import json
import logging
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = "http://localhost:8000"
ASK_ENDPOINT = f"{API_BASE_URL}/api/v1/ask"


def create_test_image() -> str:
    """Create a simple test image and return as base64"""
    # Create a simple image with text
    img = Image.new("RGB", (400, 200), color="white")
    draw = ImageDraw.Draw(img)

    # Try to use a basic font, fallback to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()

    # Add text to the image
    text = "This is a test image\nfor multimodal processing.\nWhat can you see?"
    draw.multiline_text((20, 50), text, fill="black", font=font)

    # Add some geometric shapes
    draw.rectangle([300, 50, 380, 100], outline="blue", width=3)
    draw.ellipse([300, 120, 380, 170], outline="red", width=3)

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return img_base64


def test_multimodal_request(question: str, image_b64: str = None) -> dict:
    """Test a multimodal request to the API"""
    payload = {"question": question, "collections": ["all"]}

    if image_b64:
        payload["image"] = image_b64

    headers = {"Content-Type": "application/json"}

    logger.info(f"Sending request: {question[:50]}...")
    if image_b64:
        logger.info(f"Image included: {len(image_b64)} characters")

    try:
        response = requests.post(
            ASK_ENDPOINT, json=payload, headers=headers, timeout=60
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response type: {type(result)}")

        return {"success": True, "status_code": response.status_code, "data": result}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Run comprehensive multimodal tests"""
    print("🧪 Starting Multimodal Integration Tests")
    print("=" * 50)

    # Test 1: Health check
    print("\n1. Testing API Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return

    # Test 2: Text-only request
    print("\n2. Testing Text-Only Request...")
    result = test_multimodal_request("What is machine learning?")
    if result["success"]:
        print("✅ Text-only request successful")
        answer_data = (
            json.loads(result["data"])
            if isinstance(result["data"], str)
            else result["data"]
        )
        print(f"Answer preview: {answer_data.get('answer', 'No answer')[:100]}...")
    else:
        print(f"❌ Text-only request failed: {result['error']}")

    # Test 3: Create test image
    print("\n3. Creating Test Image...")
    try:
        test_image_b64 = create_test_image()
        print(f"✅ Test image created ({len(test_image_b64)} characters)")
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        return

    # Test 4: Multimodal request with image
    print("\n4. Testing Multimodal Request with Image...")
    result = test_multimodal_request(
        "What do you see in this image? Please describe it in detail.", test_image_b64
    )
    if result["success"]:
        print("✅ Multimodal request successful")
        answer_data = (
            json.loads(result["data"])
            if isinstance(result["data"], str)
            else result["data"]
        )
        print(f"Answer preview: {answer_data.get('answer', 'No answer')[:200]}...")
    else:
        print(f"❌ Multimodal request failed: {result['error']}")

    # Test 5: Test with academic question and image
    print("\n5. Testing Academic Question with Image...")
    result = test_multimodal_request(
        "Can you help me understand the content in this image? Is it related to any course materials?",
        test_image_b64,
    )
    if result["success"]:
        print("✅ Academic multimodal request successful")
        answer_data = (
            json.loads(result["data"])
            if isinstance(result["data"], str)
            else result["data"]
        )
        print(f"Answer preview: {answer_data.get('answer', 'No answer')[:200]}...")
        print(f"Sources found: {len(answer_data.get('sources', []))}")
    else:
        print(f"❌ Academic multimodal request failed: {result['error']}")

    print("\n" + "=" * 50)
    print("🎉 Multimodal Integration Tests Complete!")
    print(
        "\nIf all tests passed, the LangChain multimodal integration is working correctly!"
    )


if __name__ == "__main__":
    main()
