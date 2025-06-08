# ******************** multimodal answer generation service ********************#
"""
Enhanced answer generation service with full multimodal support.
Uses LangChain to process both text and images directly.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..core.clients import config
from ..models.schemas import QuestionRequest
from ..services.langchain_multimodal_service import multimodal_processor
from .search_service import hybrid_search_across_collections

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)


async def multimodal_search_and_generate_answer(
    payload: QuestionRequest,
    collections: List[str],
    alpha: Optional[float] = None,
    top_k: Optional[int] = None,
    max_context_length: Optional[int] = None,
) -> str:
    """Perform hybrid search and generate answer using multimodal capabilities"""
    if max_context_length is None:
        max_context_length = config.hybrid_search.max_context_length

    # Perform hybrid search
    search_results = await hybrid_search_across_collections(
        payload, collections, alpha, top_k
    )

    # Build context from search results (if any)
    context_parts = []
    current_length = 0
    sources = []

    if search_results:
        for i, result in enumerate(search_results):
            content = result["document"].get("content", "")

            # Check if adding this content exceeds the limit
            if current_length + len(content) > max_context_length:
                # Try to add a truncated version
                remaining_space = max_context_length - current_length
                if remaining_space > 100:  # Only add if there's meaningful space
                    content = content[:remaining_space] + "..."
                    context_parts.append(f"[Source {i+1}] {content}")
                break

            context_parts.append(f"[Source {i+1}] {content}")
            current_length += len(content)

            # Collect source information
            source_info = result["document"].get(
                "url", f"Collection: {result['collection']}"
            )
            sources.append(source_info)

        context = "\n\n".join(context_parts)
        logger.info(
            f"Built context with {len(context_parts)} sources, {len(context)} characters"
        )
    else:
        context = ""
        logger.info("No search results found, proceeding with multimodal processing")

    # Prepare the multimodal prompt
    system_prompt = config.hybrid_search.prompts.assistant_system

    if context:
        user_prompt = f"""
Context from TDS course materials:
{context}

Student Question: {payload.question}

Please provide a comprehensive answer based on the provided context and any image content. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what information you can.
"""
    else:
        # No search context available, handle image or text directly
        if payload.image:
            user_prompt = f"""
Student Question: {payload.question}

Please analyze the provided image and answer the question based on what you can see in the image. If the image is related to course materials or academic content, provide a helpful explanation.
"""
        else:
            # No search results and no image - return error for text-only requests
            error_message = config.hybrid_search.fallback.error_messages.get(
                "no_results",
                "I couldn't find relevant information for your question. Please try rephrasing or asking a more specific question.",
            )
            return json.dumps({"answer": error_message, "sources": [], "links": None})

    try:
        # Use the multimodal processor for both text-only and multimodal requests
        if payload.image:
            logger.info("Processing multimodal request with image content")
            # For multimodal requests, let LangChain handle both text and image
            combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"

            answer = multimodal_processor.process_with_image(
                text=combined_prompt, base64_image=payload.image
            )
        else:
            logger.info("Processing text-only request")
            # For text-only requests, use the text processing capability
            combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"

            answer = multimodal_processor.process_text_only(combined_prompt)

        if answer:
            answer = answer.strip()
        else:
            answer = "I apologize, but I couldn't generate a proper response. Please try again."

        logger.info(f"Generated multimodal answer with {len(answer)} characters")

        # Return structured JSON response
        response_data = {
            "answer": answer,
            "sources": sources,
            "links": None,
        }

        return json.dumps(response_data)

    except Exception as e:
        logger.error(f"Error generating multimodal answer: {e}")
        error_message = config.hybrid_search.fallback.error_messages.get(
            "generation_error",
            "Sorry, I encountered an error while generating the answer.",
        )
        return json.dumps({"answer": error_message, "sources": [], "links": None})


async def direct_multimodal_answer(payload: QuestionRequest) -> str:
    """Generate answer directly using multimodal capabilities without search context"""
    try:
        if payload.image:
            logger.info("Processing direct multimodal request with image content")
            answer = multimodal_processor.process_with_image(
                text=payload.question, base64_image=payload.image
            )
        else:
            logger.info("Processing direct text request")
            answer = multimodal_processor.process_text_only(payload.question)

        if answer:
            answer = answer.strip()
        else:
            answer = "I apologize, but I couldn't generate a proper response. Please try again."

        logger.info(f"Generated direct multimodal answer with {len(answer)} characters")

        # Return structured JSON response
        response_data = {
            "answer": answer,
            "sources": [],
            "links": None,
        }

        return json.dumps(response_data)

    except Exception as e:
        logger.error(f"Error generating direct multimodal answer: {e}")
        error_message = "Sorry, I encountered an error while processing your request."
        return json.dumps({"answer": error_message, "sources": [], "links": None})
