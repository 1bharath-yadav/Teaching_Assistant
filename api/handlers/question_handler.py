# ******************** API route handlers ********************#
"""
API route handlers for the Teaching Assistant.
"""

import json
import logging
import time
import traceback
from typing import Optional

# FastAPI imports
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# ******************** application imports ********************#
from ..models.schemas import QuestionRequest, QuestionResponse
from ..services.classification_service import classify_question
from ..services.answer_service import hybrid_search_and_generate_answer
from ..core.process import process_image_with_ocr
from ..core.clients import config
from ..utils.spell_check import spell_check_and_correct

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)

# ******************** main request handler ********************#


async def handle_ask_question(
    request: Request, payload: QuestionRequest, openai_client
) -> QuestionResponse:
    """
    Handle the main question asking endpoint.
    """
    start_time = time.time()

    try:
        if payload.image:
            logger.info("Image data received with question")

        # Spell check and correct the question
        if payload.question:
            logger.info(f"Original question: {payload.question}")
            payload.question = await spell_check_and_correct(
                payload.question, openai_client
            )
            logger.info(f"Corrected question: {payload.question}")

        # Handle image and PDF processing if image is provided
        enhanced_question = payload.question
        if payload.image:
            try:
                logger.info("Processing image with OCR...")
                ocr_text = process_image_with_ocr(payload.image)
                if ocr_text:
                    enhanced_question = (
                        f"{payload.question}\n\nText extracted from image: {ocr_text}"
                    )
                    logger.info(
                        f"Enhanced question with OCR text (length: {len(enhanced_question)})"
                    )
                else:
                    logger.warning("No text extracted from image")
            except Exception as ocr_error:
                logger.error(f"OCR processing failed: {ocr_error}")
                # Continue without OCR text

        # Create enhanced payload for search
        search_payload = QuestionRequest(
            question=enhanced_question, image=payload.image
        )

        # Step 1: Classify the question to determine relevant collections
        logger.info("Classifying question to determine relevant collections...")
        classified_collections = await classify_question(search_payload)
        logger.info(f"Classified collections: {classified_collections['collections']}")

        # Step 2: Perform hybrid search and generate answer with classified collections
        logger.info("Starting hybrid search and answer generation...")
        result = await hybrid_search_and_generate_answer(
            search_payload,
            classified_collections["collections"],
            alpha=config.hybrid_search.alpha,
            top_k=config.hybrid_search.top_k,
        )

        logger.info(f"Search results type: {type(result)}")

        # Handle different result types
        if isinstance(result, str):
            try:
                result_dict = json.loads(result)
                answer = result_dict.get("answer", result)
                sources = result_dict.get("sources", None)
                links = result_dict.get("links", None)
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON parse error: {json_error}, using raw response")
                answer = result
                sources = None
                links = None
        else:
            answer = str(result)
            sources = None
            links = None

        # Log processing time
        processing_time = time.time() - start_time
        logger.info(f"Total request processing time: {processing_time:.2f} seconds")

        # Log answer preview
        answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
        logger.info(f"Returning answer preview: {answer_preview}")

        response = QuestionResponse(answer=answer, sources=sources, links=links)
        return response

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        logger.error(f"Exception type: {type(e)}")

        # Log full traceback for debugging
        logger.error(f"Full traceback: {traceback.format_exc()}")

        raise HTTPException(
            status_code=500, detail=f"Error processing your question: {str(e)}"
        )
