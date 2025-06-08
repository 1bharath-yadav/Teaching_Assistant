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
from ..services.smart_search_router import SmartSearchRouter
from ..services.answer_service import hybrid_search_and_generate_answer
from ..services.multimodal_answer_service import multimodal_search_and_generate_answer
from ..core.process import process_file_with_text_extraction
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

        # Handle multimodal questions (with images) or regular text questions
        enhanced_question = payload.question

        if payload.image:
            logger.info("Processing multimodal question with image data")

            # Initialize smart search router for collections
            search_router = SmartSearchRouter()
            search_result = await search_router.search(payload)
            search_results = search_result.get("results", [])
            search_metadata = search_result.get("metadata", {})

            # Extract collections used in search
            collections_used = list(
                set([result.get("collection", "unknown") for result in search_results])
            )

            logger.info(
                f"Search completed: {len(search_results)} results in {search_metadata.get('search_time', 0):.3f}s using {search_metadata.get('strategy_used', 'unknown')} strategy"
            )

            # Use multimodal service for answer generation
            result = await multimodal_search_and_generate_answer(
                payload,
                collections_used,
                alpha=config.hybrid_search.alpha,
                top_k=config.hybrid_search.top_k,
            )
        else:
            logger.info("Processing text-only question")

            # Create enhanced payload for search
            search_payload = QuestionRequest(
                question=enhanced_question, image=payload.image
            )

            # Initialize smart search router
            search_router = SmartSearchRouter()

            # Step 1: Use smart router to search with configured strategy
            logger.info(
                f"Using search strategy: {config.hybrid_search.search_strategy}"
            )
            search_result = await search_router.search(search_payload)

            # Extract results and metadata
            search_results = search_result.get("results", [])
            search_metadata = search_result.get("metadata", {})

            logger.info(
                f"Search completed: {len(search_results)} results in {search_metadata.get('search_time', 0):.3f}s using {search_metadata.get('strategy_used', 'unknown')} strategy"
            )

            # Step 2: Generate answer from search results
            logger.info("Starting answer generation from search results...")

            # Convert search results to the format expected by answer generation
            collections_used = list(
                set([result.get("collection", "unknown") for result in search_results])
            )

            result = await hybrid_search_and_generate_answer(
                search_payload,
                collections_used,
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
