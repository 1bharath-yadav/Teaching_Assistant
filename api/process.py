# ******************** data processing pielline ********************#
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import base64
import io
from PIL import Image
import pytesseract

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the embed/lib directory to Python path
curr_dir = Path(__file__).parent
embed_lib_path = curr_dir / ".." / "embed" / "lib"
sys.path.insert(0, str(embed_lib_path))

# Also add the parent directory to find the embed module
embed_path = curr_dir / ".."
sys.path.insert(0, str(embed_path))

# Import from your custom library
from embed.lib import generate_embedding, get_openai_client, get_typesense_client

openai_client = get_openai_client()
typesense_client = get_typesense_client  # its not function its a variable


# Request payload structure
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None  # base64-encoded


class LinkObject(BaseModel):
    url: str
    text: str


class QuestionResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None  # Keep for backward compatibility
    links: Optional[List[LinkObject]] = None  # New field for structured links


# Function definition for OpenAI function calling (updated format)
classification_function = {
    "type": "function",
    "function": {
        "name": "classify_question",
        "description": "Classify a student's query into one or more relevant TDS course collections.",
        "parameters": {
            "type": "object",
            "properties": {
                "collections": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            # misc and discourse_posts are always included
                            "data_sourcing",
                            "data_preparation",
                            "data_analysis",
                            "data_visualization",
                            "large_language_models",
                            "development_tools",
                            "deployment_tools",
                            "project-1",
                            "project-2",
                        ],
                    },
                    "description": """These are collections of typesense database to search for relevant information:
                    - project-1: Building an API(RAG) that answers student questions using course content and Discourse.
                    - project-2: Build LLMs to answer graded assignment questions.""",
                }
            },
            "required": ["collections"],
            "additionalProperties": False,
        },
    },
    "strict": True,  # Ensure strict validation of function parameters
}


async def classify_question(payload: QuestionRequest) -> Dict[str, Any]:
    """Classify question into relevant collections using OpenAI function calling"""
    messages = [
        {
            "role": "system",
            "content": "Your task is to classify the user's question into one or more relevant collections of the Data Science course.",
        },
        {"role": "user", "content": payload.question},
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,  # type: ignore
        tools=[classification_function],  # type: ignore
        tool_choice={"type": "function", "function": {"name": "classify_question"}},
    )

    # Parse function call result
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        function_args = tool_call.function.arguments
        args = json.loads(function_args)
        collections = args.get("collections", [])

        # Add default collections if not present
        default_collections = ["misc", "discourse_posts"]
        for col in default_collections:
            if col not in collections:
                collections.append(col)
        logger.info(f"Classified collections: {collections}")
    else:
        # Fallback if no tool calls - search all collections
        logger.warning("No tool calls found, using default collections.")
        collections = [
            "misc",
            "discourse_posts",
            "data_sourcing",
            "data_preparation",
            "data_analysis",
            "data_visualization",
            "large_language_models",
            "development_tools",
            "deployment_tools",
            "project-1",
            "project-2",
        ]

    return {"question": payload.question, "collections": collections}


async def hybrid_search_across_collections(
    payload: QuestionRequest,
    collections: List[str],
    alpha: float = 0.5,
    top_k: int = 10,
    query_embedding: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    """
    Optimized hybrid search using Typesense's built-in hybrid search capabilities.
    Uses multi-search with vector_query and reranking for better results.
    """
    try:
        # Generate query embedding if not provided
        if query_embedding is None:
            print("Generating query &&&&&&&&&&& embedding for hybrid search...")
            # query_embedding = generate_embedding(payload.question)

        if not query_embedding:
            logger.warning(
                "Failed to generate embedding, falling back to keyword search only."
            )
            alpha = 0.0

        all_hits = []

        # Prepare searches for multi-search with built-in hybrid search
        searches = []
        for collection in collections:
            search_params = {
                "collection": collection,
                "q": payload.question,
                "query_by": "content",  # Keyword search on content field
                "per_page": min(20, top_k * 2),  # Get more results for better ranking
                "num_typos": 2,
                # Performance optimization for long queries
                "drop_tokens_threshold": 0,
                # Enable reranking for comprehensive scoring
                "rerank_hybrid_matches": True,
            }

            # Add vector search if embeddings are available
            if query_embedding and alpha > 0:
                # Use Typesense's hybrid search with vector_query
                search_params["vector_query"] = (
                    f"embedding:([{','.join(map(str, query_embedding))}], alpha:{alpha})"
                )
                # Sort by combined fusion score (built-in hybrid scoring)
                search_params["sort_by"] = "_text_match:desc"
                print(
                    f"Using hybrid search with alpha={alpha} for collection '{collection}'"
                )
            else:
                # Pure keyword search
                search_params["sort_by"] = "_text_match:desc"

            searches.append(search_params)

        try:
            # Execute multi-search with built-in hybrid search
            logger.info(
                f"Executing optimized hybrid search across {len(collections)} collections"
            )
            multi_results = typesense_client.multi_search.perform(
                {"searches": searches}
            )

            # Process results from multi-search
            for i, collection in enumerate(collections):
                if i >= len(multi_results["results"]):
                    continue

                results = multi_results["results"][i]
                hits = results.get("hits", [])
                logger.info(f"Found {len(hits)} hits in collection '{collection}'")

                for hit in hits:
                    try:
                        document = hit.get("document", {})
                        content = document.get("content", "")

                        if (
                            not document
                            or not isinstance(content, str)
                            or not content.strip()
                        ):
                            continue

                        # Get Typesense's built-in hybrid score
                        text_match_score = hit.get("text_match", 0)
                        vector_distance = hit.get("vector_distance", None)

                        # Typesense handles the fusion scoring internally when using vector_query
                        # The text_match score is already the combined fusion score
                        hybrid_score = text_match_score / 1000000.0  # Normalize

                        hit_data = {
                            "document": document,
                            "collection": collection,
                            "hybrid_score": hybrid_score,
                            "text_match_raw": text_match_score,
                            "vector_distance": vector_distance,
                            "search_type": (
                                "hybrid" if vector_distance is not None else "keyword"
                            ),
                        }
                        all_hits.append(hit_data)

                    except Exception as hit_error:
                        logger.warning(
                            f"Error processing hit in collection '{collection}': {hit_error}"
                        )
                        continue

        except Exception as multi_search_error:
            logger.error(f"Multi-search failed: {multi_search_error}")
            # Fallback to individual keyword searches
            return await fallback_keyword_search(payload, collections, top_k)

        if not all_hits:
            logger.warning("No search results found across all collections")
            return []

        # Sort by hybrid score (Typesense's built-in fusion score)
        sorted_hits = sorted(all_hits, key=lambda x: x["hybrid_score"], reverse=True)

        # Log top results for debugging
        for i, hit in enumerate(sorted_hits[:3]):
            logger.info(
                f"Top result {i+1}: Collection='{hit['collection']}', "
                f"Hybrid={hit['hybrid_score']:.3f}, "
                f"Type={hit.get('search_type', 'unknown')}"
            )

        return sorted_hits[:top_k]

    except Exception as e:
        logger.error(f"Error in optimized_hybrid_search_across_collections: {e}")
        return []


async def fallback_keyword_search(
    payload: QuestionRequest, collections: List[str], top_k: int
) -> List[Dict[str, Any]]:
    """Fallback keyword-only search when hybrid search fails"""
    all_hits = []

    for collection in collections:
        try:
            search_params = {
                "q": payload.question,
                "query_by": "content",
                "num_typos": 2,
                "per_page": min(10, top_k),
                "sort_by": "_text_match:desc",
                "drop_tokens_threshold": 0,
            }

            logger.info(f"Fallback keyword search in collection '{collection}'")
            results = typesense_client.collections[collection].documents.search(
                search_params  # type: ignore
            )
            hits = results.get("hits", [])

            for hit in hits:
                try:
                    document = hit.get("document", {})
                    content = document.get("content", "")

                    if (
                        not document
                        or not isinstance(content, str)
                        or not content.strip()
                    ):
                        continue

                    text_match_score = hit.get("text_match", 0)
                    hybrid_score = text_match_score / 1000000.0  # Normalize

                    hit_data = {
                        "document": document,
                        "collection": collection,
                        "hybrid_score": hybrid_score,
                        "text_match_raw": text_match_score,
                        "vector_distance": None,
                        "search_type": "keyword_fallback",
                    }
                    all_hits.append(hit_data)

                except Exception as hit_error:
                    logger.warning(f"Error processing fallback hit: {hit_error}")
                    continue

        except Exception as collection_error:
            logger.error(
                f"Fallback search failed on collection '{collection}': {collection_error}"
            )
            continue

    return sorted(all_hits, key=lambda x: x["hybrid_score"], reverse=True)[:top_k]


async def hybrid_search_and_generate_answer(
    payload: QuestionRequest,
    collections: List[str],
    alpha: float = 0.5,
    top_k: int = 10,
    max_context_length: int = 30000,  # our model have 128K window size we canset upto this
) -> str:
    """
    Optimized version using Typesense's built-in hybrid search and reranking.
    Simplified context preparation and better error handling.
    """
    user_query = payload.question

    try:
        logger.info(
            f"Starting optimized hybrid search for query: '{user_query[:100]}...'"
        )
        logger.info(f"Searching collections: {collections}")
        logger.info(
            f"Parameters: alpha={alpha}, top_k={top_k}, max_context={max_context_length}"
        )

        # Step 1: Optimized hybrid search using Typesense's built-in capabilities
        top_documents = await hybrid_search_across_collections(
            payload, collections, alpha=alpha, top_k=top_k
        )
        print(top_documents)

        # Step 2: Simplified context preparation with deduplication
        context_parts = []
        total_length = 0
        used_content_hashes = set()

        for i, doc_hit in enumerate(top_documents):
            doc = doc_hit["document"]
            collection = doc_hit["collection"]
            score = doc_hit["hybrid_score"]
            content = doc.get("content", "").strip()

            if not content:
                continue

            # Simple deduplication based on content hash to check not to repeat similar content
            content_hash = hash(content[:200])  # Use first 200 chars for deduplication
            if content_hash in used_content_hashes:
                continue
            used_content_hashes.add(content_hash)

            # Format context part
            context_part = f"""--- Source {i+1}: {collection} (Score: {score:.3f}) ---
{content}

"""

            # Check context length limit
            if total_length + len(context_part) > max_context_length:
                logger.info(
                    f"Context limit reached at {total_length} characters with {len(context_parts)} sources"
                )
                break

            context_parts.append(context_part)
            total_length += len(context_part)

        context_chunks = "".join(context_parts)

        # Step 3: Generate response with structured output
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "you are datascience teaching assistant,help the student with their query using the provided course content",
                    },
                    {
                        "role": "user",
                        "content": f"""Student Query: {user_query}

                            Course Content:
                            {context_chunks}""",
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "answer_response",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "answer": {
                                    "type": "string",
                                    "description": "Comprehensive and thouhtful answer to the student's question",
                                },
                                "links": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": "string"},
                                            "text": {"type": "string"},
                                        },
                                        "required": ["url", "text"],
                                        "additionalProperties": False,
                                    },
                                    "description": "Array of relevant links found in the course content",
                                },
                            },
                            "required": ["answer", "links"],
                            "additionalProperties": False,
                        },
                    },
                },
                # max_tokens=1000,  # Adjust based on expected answer length
                # temperature=0.5,  # Moderate creativity
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            logger.info("Successfully generated answer with OpenAI")
            return content

        except Exception as openai_error:
            logger.error(f"OpenAI API error: {openai_error}")
            # Improved fallback response
            return json.dumps(
                {
                    "answer": f"I found relevant information about your question but encountered an issue generating the response. The search found {len(context_parts)} relevant sources from collections: {', '.join(collections)}. Please try asking your question again or rephrase it.",
                    "links": [],
                }
            )

    except Exception as e:
        logger.error(f"Error in hybrid_search_and_generate_answer: {e}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        return json.dumps(
            {
                "answer": "I encountered an error while processing your question. Please try again with a different phrasing or contact support if the issue persists.",
                "links": [],
            }
        )


# Optional: Add image processing function if needed
def process_image_with_ocr(base64_image: str) -> str:
    """Process base64 image and extract text using OCR"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(
            base64_image.split(",")[-1]
        )  # Remove data:image/... prefix
        image = Image.open(io.BytesIO(image_data))

        # Extract text using OCR
        extracted_text = pytesseract.image_to_string(image)
        logger.info(f"Extracted text from image: {extracted_text[:100]}...")

        return extracted_text.strip()

    except Exception as e:
        logger.error(f"Error processing image with OCR: {e}")
        return ""
