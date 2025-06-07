#!/usr/bin/env python3
"""
Updated API route handlers with streaming support using LangChain ChatOllama

This updated handler supports:
1. Streaming responses using Server-Sent Events (SSE)
2. Non-streaming responses (backward compatibility)
3. Optimized search using unified search service
4. LangChain ChatOllama integration
"""

import json
import logging
import time
import traceback
from typing import Optional

# FastAPI imports
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.responses import Response

# ******************** Application Imports ********************#
from ..models.schemas import QuestionRequest, QuestionResponse
from ..services.streaming_answer_service import (
    generate_streaming_answer,
    generate_answer_optimized,
)
from ..services.unified_search_service import unified_search
from ..core.process import process_image_with_ocr
from ..core.clients import config
from ..utils.spell_check import spell_check_and_correct

# ******************** Configuration and Logging ********************#
logger = logging.getLogger(__name__)


# ******************** Streaming Response Handler ********************#
async def handle_ask_question_streaming(
    request: Request, payload: QuestionRequest, openai_client
) -> StreamingResponse:
    """
    Handle the streaming question asking endpoint using Server-Sent Events (SSE).

    Returns streaming response with real-time answer generation.
    """

    async def generate_sse_response():
        """Generate Server-Sent Events response"""
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
                        enhanced_question = f"{payload.question}\n\nText extracted from image: {ocr_text}"
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
                question=enhanced_question,
                image=payload.image,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
                top_p=payload.top_p,
                presence_penalty=payload.presence_penalty,
                frequency_penalty=payload.frequency_penalty,
            )

            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing question...', 'done': False})}\n\n"

            # Stream answer generation
            async for chunk in generate_streaming_answer(search_payload):
                chunk_data = json.loads(chunk)

                # Format as Server-Sent Events
                yield f"data: {chunk}\n\n"

                # If this is the final chunk, break
                if chunk_data.get("done", False):
                    break

            # Send completion signal
            total_time = time.time() - start_time
            yield f"data: {json.dumps({'type': 'status', 'message': f'Completed in {total_time:.2f}s', 'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")

            error_response = {
                "type": "error",
                "error": str(e),
                "message": "Error processing your question",
                "done": True,
            }
            yield f"data: {json.dumps(error_response)}\n\n"

    return StreamingResponse(
        generate_sse_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )


# ******************** Non-Streaming Response Handler ********************#
async def handle_ask_question(
    request: Request, payload: QuestionRequest, openai_client
) -> QuestionResponse:
    """
    Handle the main question asking endpoint (non-streaming, backward compatible).

    Uses optimized LangChain ChatOllama integration.
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
            question=enhanced_question,
            image=payload.image,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            top_p=payload.top_p,
            presence_penalty=payload.presence_penalty,
            frequency_penalty=payload.frequency_penalty,
        )

        # Generate answer using optimized streaming service
        logger.info("Starting optimized answer generation...")

        result = await generate_answer_optimized(search_payload)

        logger.info(f"Answer generation result type: {type(result)}")

        # Handle result parsing
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


# ******************** Direct Search Handler ********************#
async def handle_search_only(
    request: Request, payload: QuestionRequest
) -> JSONResponse:
    """
    Handle search-only requests using optimized unified search.

    Returns search results without answer generation.
    """
    start_time = time.time()

    try:
        logger.info(f"Search-only request for: '{payload.question[:50]}...'")

        # Perform optimized unified search
        search_results = await unified_search(payload, max_results=10)

        search_time = time.time() - start_time
        logger.info(
            f"Search completed in {search_time:.3f}s, {len(search_results)} results"
        )

        # Format response
        response_data = {
            "results": search_results,
            "metadata": {
                "search_time": search_time,
                "result_count": len(search_results),
                "query": payload.question,
                "strategy": "unified_optimized",
            },
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Error in search-only request: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

        raise HTTPException(
            status_code=500, detail=f"Error performing search: {str(e)}"
        )
