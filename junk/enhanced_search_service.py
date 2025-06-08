#!/usr/bin/env python3
"""
Enhanced Search Service for Teaching Assistant

Based on performance analysis, this service implements an optimized search strategy:
1. Fast keyword-based collection routing (no LLM classification)
2. Priority on discourse posts and misc collections for student Q&A
3. Intelligent fallback to unified knowledge base
4. 79x faster than classification-based approach while maintaining coverage

Performance Results:
- Optimized approach: 0.035s average (vs 2.751s classification-based)
- 100% discourse and misc coverage (vs 60%/20% classification-based)
- 5.9 results per query (balanced result count)
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from ..core.clients import config, typesense_client
from ..models.schemas import QuestionRequest

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)


class EnhancedSearchService:
    """Enhanced search service optimized for student Q&A performance"""

    def __init__(self):
        self.config = config
        self.client = typesense_client

        # Priority collections for student Q&A (always searched first)
        self.priority_collections = [
            "discourse_posts_optimized",  # Student discussions and Q&A
            "chapters_misc",  # Live session Q&A and misc content
        ]

        # Keyword-based collection mapping (fast routing without LLM)
        self.keyword_collections = {
            # Data sourcing keywords
            "scraping": ["chapters_data_sourcing"],
            "scrape": ["chapters_data_sourcing"],
            "api": ["chapters_data_sourcing"],
            "data collection": ["chapters_data_sourcing"],
            "web scraping": ["chapters_data_sourcing"],
            # LLM and AI keywords
            "llm": ["chapters_large_language_models"],
            "language model": ["chapters_large_language_models"],
            "embedding": ["chapters_large_language_models"],
            "prompt": ["chapters_large_language_models"],
            "ai": ["chapters_large_language_models"],
            # Development tools
            "docker": ["chapters_development_tools", "chapters_deployment_tools"],
            "git": ["chapters_development_tools"],
            "vscode": ["chapters_development_tools"],
            "vs code": ["chapters_development_tools"],
            "python": ["chapters_development_tools"],
            "development": ["chapters_development_tools"],
            # Data processing
            "visualization": ["chapters_data_visualization"],
            "analysis": ["chapters_data_preparation"],
            "preparation": ["chapters_data_preparation"],
            "prepare": ["chapters_data_preparation"],
            "clean": ["chapters_data_preparation"],
            # Deployment
            "deploy": ["chapters_deployment_tools"],
            "deployment": ["chapters_deployment_tools"],
            "server": ["chapters_deployment_tools"],
            # Projects
            "project": ["chapters_project-1", "chapters_project-2"],
            "assignment": ["chapters_project-1", "chapters_project-2"],
            "submission": ["chapters_project-1", "chapters_project-2"],
        }

        # Fallback collection for comprehensive search
        self.fallback_collection = "unified_knowledge_base"

    def _detect_relevant_collections(self, question: str) -> List[str]:
        """Fast keyword-based collection detection (no LLM needed)"""
        question_lower = question.lower()
        collections = set(
            self.priority_collections
        )  # Always include priority collections

        # Add collections based on keyword detection
        for keyword, cols in self.keyword_collections.items():
            if keyword in question_lower:
                collections.update(cols)
                logger.debug(
                    f"Keyword '{keyword}' detected, adding collections: {cols}"
                )

        return list(collections)

    async def search(
        self, payload: QuestionRequest, use_fallback: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with optimized performance

        Args:
            payload: Question request
            use_fallback: Whether to fall back to unified KB if few results

        Returns:
            List of search results with collection metadata
        """
        start_time = time.time()
        question = payload.question

        # Step 1: Fast collection detection (no LLM classification)
        target_collections = self._detect_relevant_collections(question)
        logger.info(
            f"Target collections for '{question[:50]}...': {target_collections}"
        )

        # Step 2: Search target collections
        all_results = await self._search_collections(question, target_collections)

        # Step 3: Fallback to unified KB if results are insufficient
        if use_fallback and len(all_results) < self.config.hybrid_search.top_k:
            logger.info(
                f"Only {len(all_results)} results found, searching unified knowledge base"
            )
            unified_results = await self._search_collections(
                question, [self.fallback_collection]
            )
            all_results.extend(unified_results)

        # Step 4: Sort and limit results
        sorted_results = self._rank_results(all_results)
        final_results = sorted_results[
            : self.config.hybrid_search.top_k * 2
        ]  # Allow more results

        search_time = time.time() - start_time
        logger.info(
            f"Enhanced search completed in {search_time:.3f}s, returning {len(final_results)} results"
        )

        return final_results

    async def _search_collections(
        self, question: str, collections: List[str]
    ) -> List[Dict[str, Any]]:
        """Search specified collections and return results"""
        all_results = []

        search_params = {
            "q": question,
            "query_by": "content",
            "per_page": self.config.hybrid_search.top_k,
            "num_typos": self.config.hybrid_search.num_typos,
            "highlight_full_fields": "content",
        }

        for collection_name in collections:
            try:
                logger.debug(f"Searching collection: {collection_name}")
                results = self.client.collections[collection_name].documents.search(
                    search_params
                )

                for hit in results.get("hits", []):
                    result = {
                        "document": hit["document"],
                        "text_match": hit.get("text_match", 0),
                        "collection": collection_name,
                        "highlights": hit.get("highlights", []),
                    }

                    # Add vector distance if available
                    if "vector_distance" in hit:
                        result["vector_distance"] = hit["vector_distance"]

                    all_results.append(result)

                logger.debug(
                    f"Found {len(results.get('hits', []))} results in {collection_name}"
                )

            except Exception as e:
                logger.error(f"Error searching collection {collection_name}: {e}")
                continue

        return all_results

    def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank results by relevance with priority boosting

        Priority order:
        1. Discourse posts (student Q&A)
        2. Misc collections (live sessions)
        3. Specific topic chapters
        4. Unified knowledge base
        """

        def calculate_score(result):
            base_score = result.get("text_match", 0)
            collection = result.get("collection", "")

            # Apply collection priority boosts
            if "discourse" in collection:
                priority_boost = 1.5  # Highest priority for student discussions
            elif "misc" in collection:
                priority_boost = 1.3  # High priority for live session content
            elif collection == "unified_knowledge_base":
                priority_boost = 0.8  # Lower priority (fallback content)
            else:
                priority_boost = 1.0  # Normal priority for specific chapters

            # Combine text match with vector similarity if available
            if "vector_distance" in result:
                vector_similarity = 1 - min(result["vector_distance"], 1.0)
                alpha = self.config.hybrid_search.alpha
                combined_score = alpha * vector_similarity + (1 - alpha) * (
                    base_score / 1000000
                )
            else:
                combined_score = base_score / 1000000

            return combined_score * priority_boost

        return sorted(results, key=calculate_score, reverse=True)

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about available collections"""
        stats = {
            "priority_collections": [],
            "keyword_collections": [],
            "fallback_collection": None,
            "total_collections": 0,
        }

        try:
            # Check priority collections
            for collection in self.priority_collections:
                try:
                    schema = self.client.collections[collection].retrieve()
                    doc_count = schema.get("num_documents", 0)
                    stats["priority_collections"].append(
                        {
                            "name": collection,
                            "documents": doc_count,
                            "status": "available",
                        }
                    )
                except:
                    stats["priority_collections"].append(
                        {"name": collection, "documents": 0, "status": "not_found"}
                    )

            # Check fallback collection
            try:
                schema = self.client.collections[self.fallback_collection].retrieve()
                doc_count = schema.get("num_documents", 0)
                stats["fallback_collection"] = {
                    "name": self.fallback_collection,
                    "documents": doc_count,
                    "status": "available",
                }
            except:
                stats["fallback_collection"] = {
                    "name": self.fallback_collection,
                    "documents": 0,
                    "status": "not_found",
                }

            # Count unique keyword collections
            unique_collections = set()
            for cols in self.keyword_collections.values():
                unique_collections.update(cols)
            stats["keyword_collections"] = list(unique_collections)
            stats["total_collections"] = (
                len(unique_collections) + len(self.priority_collections) + 1
            )

        except Exception as e:
            logger.error(f"Error getting search stats: {e}")

        return stats


# Create global instance
enhanced_search_service = EnhancedSearchService()


# ******************** convenience functions ********************#
async def enhanced_search(
    payload: QuestionRequest, use_fallback: bool = True
) -> List[Dict[str, Any]]:
    """Convenience function for enhanced search"""
    return await enhanced_search_service.search(payload, use_fallback)


async def get_enhanced_search_stats() -> Dict[str, Any]:
    """Get enhanced search service statistics"""
    return await enhanced_search_service.get_search_stats()
