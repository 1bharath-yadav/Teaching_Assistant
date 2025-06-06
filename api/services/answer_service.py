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
        # Generate answer using the configured model
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.llm_hyperparameters.answer_generation.temperature,
            max_tokens=config.llm_hyperparameters.answer_generation.max_tokens,
        )

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
                link_text = doc.get("title", doc.get("id", "Reference"))
                if link_text == doc.get("id"):
                    # Try to extract a better title from content
                    content = doc.get("content", "")[:100]
                    if content:
                        link_text = content.split("\n")[0].strip()
                        if len(link_text) > 50:
                            link_text = link_text[:50] + "..."

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
