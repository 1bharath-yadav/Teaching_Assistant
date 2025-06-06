#!/usr/bin/env python3
"""
Test script for EasyOCR integration in the Teaching Assistant API
"""

import base64
import json
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.core.process import process_image_with_ocr, process_image_with_metadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_image():
    """Create a simple test image with text using PIL"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.error("PIL not available, cannot create test image")
        return None

    # Create a simple image with text
    img = Image.new("RGB", (400, 200), color="white")
    draw = ImageDraw.Draw(img)

    # Try to use a default font
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()

    # Draw some text
    text_lines = [
        "Tools in Data Science",
        "Course Materials",
        "Data Preprocessing",
        "Machine Learning",
    ]

    y_offset = 30
    for line in text_lines:
        draw.text((50, y_offset), line, fill="black", font=font)
        y_offset += 30

    # Save test image
    test_image_path = project_root / "test_image.png"
    img.save(test_image_path)
    logger.info(f"Created test image: {test_image_path}")
    return test_image_path


def test_ocr_integration():
    """Test the OCR integration"""
    logger.info("Testing EasyOCR integration...")

    # Create test image
    test_image_path = create_test_image()
    if not test_image_path:
        logger.error("Failed to create test image")
        return

    try:
        # Test with base64 encoded image
        logger.info("Testing with base64 encoded image...")
        with open(test_image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        # Test basic OCR function
        logger.info("Testing process_image_with_ocr...")
        extracted_text = process_image_with_ocr(f"data:image/png;base64,{img_base64}")
        logger.info(f"Extracted text: {extracted_text}")

        # Test metadata OCR function
        logger.info("Testing process_image_with_metadata...")
        metadata_result = process_image_with_metadata(
            f"data:image/png;base64,{img_base64}"
        )
        logger.info(f"Metadata result: {json.dumps(metadata_result, indent=2)}")

        # Clean up
        test_image_path.unlink()
        logger.info("Test completed successfully!")

    except Exception as e:
        logger.error(f"OCR test failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    test_ocr_integration()
