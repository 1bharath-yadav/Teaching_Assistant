# ******************** answer generation service ********************#
"""
Service for generating answers from search results using language models.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from ..core.clients import config, openai_client
from ..models.schemas import QuestionRequest, LinkObject
from .search_service import hybrid_search_across_collections

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)


# ******************** answer generation functions ********************#
async def hybrid_search_and_generate_answer(
    payload: QuestionRequest,
    collections: List[str],
    alpha: Optional[float] = None,
    top_k: Optional[int] = None,
    max_context_length: Optional[int] = None,
) -> str:
    """Perform hybrid search and generate answer using retrieved context"""
    if max_context_length is None:
        max_context_length = config.hybrid_search.max_context_length

    # Perform hybrid search
    search_results = await hybrid_search_across_collections(
        payload, collections, alpha, top_k
    )

    if not search_results:
        error_message = config.hybrid_search.fallback.error_messages.get(
            "no_results",
            "I couldn't find relevant information for your question. Please try rephrasing or asking a more specific question.",
        )
        return json.dumps({"answer": error_message, "sources": [], "links": None})

    # Build context from search results
    context_parts = []
    current_length = 0
    sources = []

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

    # Get the configured model for chat
    chat_model = config.defaults.chat_provider
    if chat_model == "ollama":
        model_name = config.ollama.default_model
    elif chat_model == "openai":
        model_name = config.openai.default_model
    elif chat_model == "azure":
        model_name = config.azure.deployment_name or config.openai.default_model
    else:
        model_name = config.openai.default_model  # fallback

    # Build the prompt
    system_prompt = config.hybrid_search.prompts.assistant_system
    user_prompt = f"""
Context from TDS course materials:
{context}

Student Question: {payload.question}

Please provide a comprehensive answer based on the provided context. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what information you can.
"""

    try:
        # Use request parameters with fallback to config values
        temperature = (
            payload.temperature
            if payload.temperature is not None
            else config.llm_hyperparameters.answer_generation.temperature
        )
        max_tokens = (
            payload.max_tokens
            if payload.max_tokens is not None
            else config.llm_hyperparameters.answer_generation.max_tokens
        )

        # For streaming responses, use the streaming service
        if chat_model == "ollama":
            # Import streaming service here to avoid circular imports
            from .streaming_answer_service import generate_answer_optimized

            return await generate_answer_optimized(payload, max_context_length)

        # Build OpenAI parameters for non-streaming
        openai_params = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add optional parameters if provided in request
        if payload.top_p is not None:
            openai_params["top_p"] = payload.top_p
        if payload.presence_penalty is not None:
            openai_params["presence_penalty"] = payload.presence_penalty
        if payload.frequency_penalty is not None:
            openai_params["frequency_penalty"] = payload.frequency_penalty

        # Generate answer using the configured model
        response = openai_client.chat.completions.create(**openai_params)

        answer = response.choices[0].message.content
        if answer:
            answer = answer.strip()
        else:
            answer = "I apologize, but I couldn't generate a proper response. Please try again."

        # Enhanced link extraction if enabled
        if config.hybrid_search.answer_generation.enable_link_extraction:
            answer = await enhance_answer_with_links(answer, search_results)

        logger.info(f"Generated answer with {len(answer)} characters")

        # Return structured JSON response
        response_data = {
            "answer": answer,
            "sources": sources,
            "links": None,  # Links are embedded in answer if link extraction is enabled
        }

        return json.dumps(response_data)

    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        error_message = config.hybrid_search.fallback.error_messages.get(
            "generation_error",
            "Sorry, I encountered an error while generating the answer.",
        )
        return json.dumps({"answer": error_message, "sources": [], "links": None})


async def enhance_answer_with_links(
    answer: str, search_results: List[Dict[str, Any]]
) -> str:
    """Enhance the answer with relevant links from search results"""
    try:
        links = []
        for result in search_results[:3]:  # Only use top 3 results for links
            doc = result["document"]
            if "url" in doc and doc["url"]:
                # Create a meaningful link text
                link_text = doc.get("title") or doc.get("id", "Reference")
                if link_text == doc.get("id") or not link_text:
                    # Try to extract a better title from content
                    content = doc.get("content", "") or ""
                    if content:
                        # Clean HTML tags and entities from content
                        clean_content = re.sub(r"<[^>]+>", "", content)
                        clean_content = re.sub(r"&[a-zA-Z0-9#]+;", "", clean_content)

                        # Get first meaningful line or sentence
                        lines = clean_content.split("\n")
                        for line in lines:
                            line = line.strip()
                            if line and len(line) > 10:  # Skip very short lines
                                # Fix spacing issues (missing spaces after periods)
                                line = re.sub(r"([.!?])([A-Z])", r"\1 \2", line)

                                # Try to get first sentence or meaningful chunk
                                sentences = re.split(r"[.!?]\s+", line)
                                if sentences and len(sentences[0]) > 15:
                                    link_text = sentences[0]
                                    # Ensure it ends with proper punctuation
                                    if not link_text.endswith((".", "!", "?")):
                                        link_text += "..."
                                else:
                                    # For shorter content, clean up spacing
                                    link_text = re.sub(r"\s+", " ", line)
                                break

                        # Truncate if too long
                        if len(link_text) > 60:
                            link_text = link_text[:57] + "..."

                # Final cleanup - remove any remaining HTML entities and extra whitespace
                if link_text:
                    link_text = re.sub(r"&[a-zA-Z0-9#]+;", "", link_text)
                    link_text = " ".join(link_text.split())

                # Ensure we have a reasonable fallback
                if not link_text or len(link_text.strip()) < 5:
                    link_text = "Course Material"

                links.append(LinkObject(url=doc["url"], text=link_text))

        if links:
            link_section = "\n\n**Related Resources:**\n"
            for link in links:
                link_section += f"- [{link.text}]({link.url})\n"

            return answer + link_section

        return answer

    except Exception as e:
        logger.warning(f"Failed to enhance answer with links: {e}")
        return answer
