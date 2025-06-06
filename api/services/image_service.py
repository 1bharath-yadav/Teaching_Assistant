# ******************** image processing service ********************#
"""
Enhanced image processing service for OCR and text extraction.
"""

import base64
import hashlib
import io
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)

# ******************** optional dependencies ********************#
try:
    import easyocr

    EASYOCR_AVAILABLE = True
    logger.info("EasyOCR library is available")
except ImportError:
    easyocr = None
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR library not available - using basic fallback")


# ******************** image processing class ********************#
class EnhancedImageProcessor:
    """Enhanced image processor with OCR capabilities."""

    def __init__(self, use_ocr=True, ocr_languages=None):
        self.use_ocr = use_ocr and EASYOCR_AVAILABLE
        self.ocr_languages = ocr_languages or ["en"]

        if self.use_ocr and easyocr is not None:
            try:
                self.ocr_reader = easyocr.Reader(self.ocr_languages)
                logger.info(f"EasyOCR initialized with languages: {self.ocr_languages}")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.use_ocr = False

    def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using OCR or fallback method"""
        if not self.use_ocr:
            return ""

        try:
            # Convert bytes to PIL Image for OCR
            image = Image.open(io.BytesIO(image_data))

            # Use EasyOCR for text extraction
            try:
                results = self.ocr_reader.readtext(image_data)
                extracted_text = []

                for bbox, text, confidence in results:
                    # Filter out low-confidence detections
                    try:
                        conf_score = (
                            float(confidence) if confidence is not None else 0.0
                        )
                        if conf_score > 0.5:
                            extracted_text.append(text)
                        else:
                            # For debugging, log low-confidence text
                            logger.debug(
                                f"Low confidence text: {text} (confidence: {confidence})"
                            )
                    except (ValueError, TypeError):
                        continue

                result_text = " ".join(extracted_text)
                if result_text:
                    logger.info(f"Extracted text from image: {result_text[:100]}...")
                return result_text

            except Exception as e:
                logger.error(f"Failed to extract text from image: {e}")
                return ""

        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            return ""

    def process_base64_image(self, base64_image: str) -> Dict[str, Any]:
        """Process base64 image and return extracted information"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image.split(",")[-1])

            # Extract text using OCR
            extracted_text = self.extract_text_from_image(image_data)

            # Generate image info
            image_id = hashlib.md5(base64_image[:100].encode()).hexdigest()[:12]

            return {
                "image_id": image_id,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "ocr_enabled": self.use_ocr,
                "processing_successful": True,
            }

        except Exception as e:
            logger.error(f"Error processing base64 image: {e}")
            return {
                "image_id": "unknown",
                "extracted_text": "",
                "text_length": 0,
                "ocr_enabled": self.use_ocr,
                "processing_successful": False,
                "error": str(e),
            }

    def process_image_with_metadata(
        self, base64_image: str, include_metadata=True
    ) -> Dict[str, Any]:
        """Process image and return comprehensive metadata"""
        try:
            # Get basic processing results
            result = self.process_base64_image(base64_image)

            if include_metadata:
                result.update(
                    {
                        "timestamp": time.time(),
                        "ocr_method": "easyocr" if self.use_ocr else "none",
                        "languages_supported": (
                            self.ocr_languages if self.use_ocr else []
                        ),
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error processing image with metadata: {e}")
            return {
                "image_id": "error",
                "extracted_text": "",
                "text_length": 0,
                "ocr_enabled": False,
                "processing_successful": False,
                "error": str(e),
                "timestamp": time.time(),
                "ocr_method": "error",
            }


# ******************** global image processor instance ********************#
image_processor = EnhancedImageProcessor(use_ocr=True, ocr_languages=["en"])
