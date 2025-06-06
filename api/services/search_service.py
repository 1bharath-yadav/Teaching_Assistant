# ******************** search service ********************#
"""
Hybrid search service for performing vector and text search across collections.
"""

import logging
from typing import Any, Dict, List, Optional

from ..core.clients import config, typesense_client
from ..models.schemas import QuestionRequest
from lib.embeddings import generate_embedding

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)


# ******************** hybrid search functions ********************#
async def hybrid_search_across_collections(
    payload: QuestionRequest,
    collections: List[str],
    alpha: Optional[float] = None,
    top_k: Optional[int] = None,
    query_embedding: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    """Perform hybrid search across multiple collections"""
    if alpha is None:
        alpha = config.hybrid_search.alpha
    if top_k is None:
        top_k = config.hybrid_search.top_k

    all_results = []

    # Generate embedding for the query if not provided
    if query_embedding is None:
        try:
            query_embedding = generate_embedding(payload.question)
            logger.info(f"Generated embedding for query: {payload.question[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            query_embedding = None

    for collection_name in collections:
        try:
            logger.info(f"Searching in collection: {collection_name}")

            search_params = {
                "q": payload.question,
                "query_by": "content",
                "num_typos": config.hybrid_search.num_typos,
                "highlight_full_fields": "content",
                "limit": top_k,
                "exhaustive_search": True,
                "drop_tokens_threshold": 0,
                "typo_tokens_threshold": 2,
            }

            # Use multi_search endpoint to avoid 4000 character limit with embeddings
            try:
                if query_embedding:
                    # Use multi_search for hybrid search with embeddings to avoid 4000 char limit
                    vector_query = f"embedding:([{','.join(map(str, query_embedding))}], alpha: {alpha})"

                    # Create separate multi_search params (different from regular search params)
                    multi_search_params = {
                        "collection": collection_name,
                        "q": payload.question,
                        "query_by": "content",
                        "vector_query": vector_query,
                        "num_typos": config.hybrid_search.num_typos,
                        "highlight_full_fields": "content",
                        "limit": top_k,
                        "exhaustive_search": True,
                        "drop_tokens_threshold": 0,
                        "typo_tokens_threshold": 2,
                        "exclude_fields": "embedding",  # Optimize bandwidth
                    }

                    logger.info(f"Hybrid search enabled with alpha={alpha}")

                    # Use multi_search endpoint with proper structure
                    multi_search_request = {"searches": [multi_search_params]}
                    multi_search_response = typesense_client.multi_search.perform(
                        multi_search_request
                    )

                    # Extract results from multi_search response
                    if (
                        multi_search_response
                        and isinstance(multi_search_response, dict)
                        and "results" in multi_search_response
                        and len(multi_search_response["results"]) > 0
                    ):
                        search_results = multi_search_response["results"][0]
                    else:
                        search_results = {"hits": []}

                else:
                    # Use regular search for text-only queries (no vector, should fit in 4000 chars)
                    logger.info("Text-only search (no embedding)")
                    search_results = typesense_client.collections[
                        collection_name
                    ].documents.search(search_params)

                # Process results
                for hit in search_results.get("hits", []):
                    hit_data = {
                        "document": hit["document"],
                        "text_match": hit.get("text_match", 0),
                        "collection": collection_name,
                    }

                    # Add vector distance if available
                    if "vector_distance" in hit:
                        hit_data["vector_distance"] = hit["vector_distance"]

                    all_results.append(hit_data)

                logger.info(
                    f"Found {len(search_results.get('hits', []))} results in {collection_name}"
                )

            except Exception as e:
                logger.error(f"Search failed for collection {collection_name}: {e}")
                continue

        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            continue

    # Sort results by relevance (combine text match and vector similarity)
    def calculate_relevance_score(result):
        text_score = result.get("text_match", 0)

        # If vector distance is available, convert it to similarity score
        if "vector_distance" in result:
            vector_similarity = 1 - min(result["vector_distance"], 1.0)
            # Combine text and vector scores based on alpha
            return alpha * vector_similarity + (1 - alpha) * (text_score / 1000000)
        else:
            return text_score / 1000000

    sorted_results = sorted(all_results, key=calculate_relevance_score, reverse=True)

    # Limit to top_k results
    final_results = sorted_results[:top_k]

    logger.info(
        f"Returning {len(final_results)} total results from {len(collections)} collections"
    )
    return final_results
