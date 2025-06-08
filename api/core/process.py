# ******************** data processing pipeline ********************#
"""
Legacy process module - simplified after modularization.
Contains backward compatibility functions for existing handlers.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)

# ******************** modular service imports ********************#
from ..models.schemas import QuestionRequest, QuestionResponse, LinkObject
from ..services.langchain_multimodal_service import (
    multimodal_processor,
    process_image_with_ocr as langchain_process_image_with_ocr,
    process_file_with_text_extraction as langchain_process_file_with_text_extraction,
    process_image_with_metadata as langchain_process_image_with_metadata,
)
from ..services.classification_service import classify_question
from ..services.search_service import hybrid_search_across_collections
from ..services.answer_service import hybrid_search_and_generate_answer

# ******************** global service instances ********************#
# Use simplified LangChain multimodal processor
image_processor = multimodal_processor


# ******************** backward compatibility functions ********************#
def process_image_with_ocr(base64_image: str) -> str:
    """Process base64 image and extract text using LangChain multimodal capabilities"""
    try:
        # Use the simplified LangChain processor
        return langchain_process_image_with_ocr(base64_image)
    except Exception as e:
        logger.error(f"Error processing image with OCR: {e}")
        return ""


def process_file_with_text_extraction(base64_data: str) -> str:
    """Process base64 file (image or PDF) and extract text using LangChain multimodal capabilities"""
    try:
        # Use the simplified LangChain processor
        return langchain_process_file_with_text_extraction(base64_data)
    except Exception as e:
        logger.error(f"Error processing file with text extraction: {e}")
        return ""


def process_image_with_metadata(base64_image: str) -> Dict[str, Any]:
    """Process base64 image and return detailed metadata along with extracted text"""
    try:
        result = langchain_process_image_with_metadata(base64_image)

        # Enhance with additional metadata for backward compatibility
        result.update(
            {
                "timestamp": time.time(),
                "ocr_method": result.get("processor", "langchain_multimodal"),
                "languages_supported": [
                    "en"
                ],  # LangChain models typically support many languages
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


# ******************** legacy wrapper functions ********************#
# These functions maintain backward compatibility with existing handlers


async def process_question_request(payload: QuestionRequest) -> QuestionResponse:
    """
    Legacy wrapper function for complete question processing.
    Uses the new modular services internally.
    """
    try:
        # Step 1: Classify the question
        classification_result = await classify_question(payload)
        collections = classification_result.get("collections", ["misc"])

        # Step 2: Generate answer using the modular service
        answer_json = await hybrid_search_and_generate_answer(
            payload=payload, collections=collections
        )

        # Parse the JSON response from the answer service
        answer_data = (
            json.loads(answer_json) if isinstance(answer_json, str) else answer_json
        )

        # Convert to response format
        links = [LinkObject(**link) for link in answer_data.get("links", [])]

        return QuestionResponse(answer=answer_data.get("answer", ""), links=links)

    except Exception as e:
        logger.error(f"Error in process_question_request: {e}")
        return QuestionResponse(
            answer="I encountered an error while processing your question. Please try again.",
            links=[],
        )


# ******************** direct service access functions ********************#
# These provide direct access to the modular services

# Re-export the main service functions for backward compatibility
__all__ = [
    "QuestionRequest",
    "QuestionResponse",
    "LinkObject",
    "classify_question",
    "hybrid_search_across_collections",
    "hybrid_search_and_generate_answer",
    "process_image_with_ocr",
    "process_file_with_text_extraction",
    "process_image_with_metadata",
    "process_question_request",
    "image_processor",  # This is now the LangChain multimodal processor
    "multimodal_processor",  # Direct access to the new processor
]
