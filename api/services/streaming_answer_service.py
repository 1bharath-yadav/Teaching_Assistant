#!/usr/bin/env python3
"""
Streaming Answer Service with LangChain ChatOllama Integration

Optimized based on raw data analysis:
1. Uses clean_content instead of raw content processing
2. Eliminates unnecessary content type detection (uses pre-computed fields)
3. Implements streaming responses with LangChain ChatOllama
4. Consistent embedding exclusion for performance
5. Enhanced context building with proper HTML cleaning
"""

import json
import logging
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from ..core.clients import config
from ..models.schemas import QuestionRequest, LinkObject
from .unified_search_service import unified_search

# ******************** Configuration and Logging ********************#
logger = logging.getLogger(__name__)


class StreamingAnswerService:
    """Streaming answer service using LangChain ChatOllama"""

    def __init__(self):
        self.config = config

        # Initialize ChatOllama with streaming support
        self.llm = ChatOllama(
            model=self.config.ollama.default_model,
            base_url=self.config.ollama.base_url,
            temperature=self.config.llm_hyperparameters.answer_generation.temperature,
            # Enable streaming by default
            streaming=True,
        )

        # Create chat prompt template
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.config.hybrid_search.prompts.assistant_system),
                (
                    "human",
                    """Context from TDS course materials:
{context}

Student Question: {question}

Please provide a comprehensive answer based on the provided context. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what information you can.""",
                ),
            ]
        )

    async def generate_streaming_answer(
        self, payload: QuestionRequest, max_context_length: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming answer with optimized search and context building

        Args:
            payload: Question request
            max_context_length: Maximum context length

        Yields:
            Streaming answer chunks
        """
        start_time = time.time()

        if max_context_length is None:
            max_context_length = self.config.hybrid_search.max_context_length

        logger.info(
            f"Starting streaming answer generation for: '{payload.question[:50]}...'"
        )

        try:
            # Step 1: Perform optimized unified search
            search_results = await unified_search(payload, max_results=15)

            if not search_results:
                error_message = self.config.hybrid_search.fallback.error_messages.get(
                    "no_results",
                    "I couldn't find relevant information for your question. Please try rephrasing or asking a more specific question.",
                )
                yield json.dumps(
                    {"answer": error_message, "sources": [], "links": None}
                )
                return

            # Step 2: Build optimized context using clean_content
            context, sources = self._build_optimized_context(
                search_results, max_context_length
            )

            search_time = time.time() - start_time
            logger.info(f"Search and context building completed in {search_time:.3f}s")

            # Step 3: Update LLM parameters from request
            self._update_llm_parameters(payload)

            # Step 4: Create prompt
            messages = self.prompt_template.format_messages(
                context=context, question=payload.question
            )

            # Step 5: Stream response
            answer_chunks = []
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    answer_chunks.append(chunk.content)
                    # Yield streaming chunk
                    yield json.dumps(
                        {"type": "chunk", "content": chunk.content, "done": False}
                    )

            # Step 6: Post-process complete answer
            complete_answer = "".join(answer_chunks).strip()

            if not complete_answer:
                complete_answer = "I apologize, but I couldn't generate a proper response. Please try again."

            # Step 7: Enhance with links if enabled
            if self.config.hybrid_search.answer_generation.enable_link_extraction:
                complete_answer = await self._enhance_answer_with_links(
                    complete_answer, search_results
                )

            total_time = time.time() - start_time
            logger.info(
                f"Streaming answer generation completed in {total_time:.3f}s, answer length: {len(complete_answer)}"
            )

            # Yield final response
            yield json.dumps(
                {
                    "type": "complete",
                    "answer": complete_answer,
                    "sources": sources,
                    "links": None,
                    "done": True,
                    "generation_time": total_time,
                }
            )

        except Exception as e:
            logger.error(f"Error in streaming answer generation: {e}")
            error_message = self.config.hybrid_search.fallback.error_messages.get(
                "generation_error",
                "Sorry, I encountered an error while generating the answer.",
            )
            yield json.dumps(
                {
                    "type": "error",
                    "answer": error_message,
                    "sources": [],
                    "links": None,
                    "error": str(e),
                    "done": True,
                }
            )

    async def generate_answer(
        self, payload: QuestionRequest, max_context_length: Optional[int] = None
    ) -> str:
        """
        Generate non-streaming answer (for backward compatibility)

        Args:
            payload: Question request
            max_context_length: Maximum context length

        Returns:
            JSON string with answer and metadata
        """
        # Collect all streaming chunks into complete answer
        chunks = []
        final_response = None

        async for chunk in self.generate_streaming_answer(payload, max_context_length):
            chunk_data = json.loads(chunk)
            if chunk_data.get("type") == "chunk":
                chunks.append(chunk_data.get("content", ""))
            elif chunk_data.get("type") in ["complete", "error"]:
                final_response = chunk_data
                break

        if final_response:
            return json.dumps(
                {
                    "answer": final_response.get("answer", ""),
                    "sources": final_response.get("sources", []),
                    "links": final_response.get("links"),
                    "generation_time": final_response.get("generation_time"),
                }
            )
        else:
            # Fallback if streaming failed
            return json.dumps(
                {
                    "answer": "".join(chunks) if chunks else "Error generating answer",
                    "sources": [],
                    "links": None,
                }
            )

    def _build_optimized_context(
        self, search_results: List[Dict[str, Any]], max_length: int
    ) -> tuple[str, List[str]]:
        """
        Build optimized context using clean_content and pre-computed fields

        Optimizations based on raw data analysis:
        1. Use clean_content instead of content for better quality
        2. Use pre-computed content_type and source_type fields
        3. No unnecessary content processing
        """
        context_parts = []
        current_length = 0
        sources = []

        for i, result in enumerate(search_results):
            document = result["document"]

            # Use clean_content when available, fallback to content
            content = document.get("clean_content") or document.get("content", "")

            # Skip empty content
            if not content.strip():
                continue

            # Use pre-computed fields (no unnecessary detection)
            content_type = document.get("content_type", "general")
            source_type = document.get("source_type", "unknown")

            # Check if adding this content exceeds the limit
            if current_length + len(content) > max_length:
                # Try to add a truncated version
                remaining_space = max_length - current_length
                if remaining_space > 100:  # Only add if there's meaningful space
                    content = content[:remaining_space] + "..."
                    context_parts.append(f"[Source {i+1}] ({content_type}) {content}")
                break

            context_parts.append(f"[Source {i+1}] ({content_type}) {content}")
            current_length += len(content)

            # Collect source information
            source_info = document.get(
                "url", f"Collection: {result.get('collection', 'unknown')}"
            )
            sources.append(source_info)

        context = "\n\n".join(context_parts)

        logger.info(
            f"Built optimized context with {len(context_parts)} sources, {len(context)} characters"
        )

        return context, sources

    def _update_llm_parameters(self, payload: QuestionRequest):
        """Update LLM parameters from request payload"""
        # Update temperature if provided
        if payload.temperature is not None:
            self.llm.temperature = payload.temperature

        # Note: ChatOllama doesn't support all OpenAI parameters
        # We can extend this as needed for other supported parameters

    async def _enhance_answer_with_links(
        self, answer: str, search_results: List[Dict[str, Any]]
    ) -> str:
        """
        Enhance answer with relevant links from search results

        Optimized to use clean_content for better link text extraction
        """
        try:
            links = []
            for result in search_results[:3]:  # Only use top 3 results for links
                doc = result["document"]
                if "url" in doc and doc["url"]:
                    # Create meaningful link text using clean_content
                    link_text = doc.get("title") or doc.get("id", "Reference")

                    if link_text == doc.get("id") or not link_text:
                        # Use clean_content for better text extraction
                        content = doc.get("clean_content") or doc.get("content", "")
                        if content:
                            # Get first meaningful line or sentence from clean content
                            lines = content.split("\n")
                            for line in lines:
                                line = line.strip()
                                if line and len(line) > 10:  # Skip very short lines
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

                    # Final cleanup
                    if link_text:
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


# Create global instance
streaming_answer_service = StreamingAnswerService()


# ******************** Convenience Functions ********************#
async def generate_streaming_answer(
    payload: QuestionRequest, max_context_length: Optional[int] = None
) -> AsyncGenerator[str, None]:
    """Convenience function for streaming answer generation"""
    async for chunk in streaming_answer_service.generate_streaming_answer(
        payload, max_context_length
    ):
        yield chunk


async def generate_answer_optimized(
    payload: QuestionRequest, max_context_length: Optional[int] = None
) -> str:
    """Convenience function for optimized answer generation (non-streaming)"""
    return await streaming_answer_service.generate_answer(payload, max_context_length)


async def hybrid_search_and_generate_streaming_answer(
    payload: QuestionRequest,
    max_context_length: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """
    Backward-compatible function name for streaming answer generation

    This replaces the old hybrid_search_and_generate_answer with streaming support
    """
    async for chunk in generate_streaming_answer(payload, max_context_length):
        yield chunk
