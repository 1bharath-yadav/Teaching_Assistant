#!/usr/bin/env python3
"""
Smart Search Router for Teaching Assistant

This service dynamically routes search requests to the optimal search strategy
based on configuration settings. Supports three search approaches:

1. Classification-based: Original LLM classification (slow but targeted)
2. Enhanced keyword-based: Fast routing with fallback (balanced)
3. Unified knowledge base: Direct comprehensive search (fastest)

The router automatically selects the configured strategy and provides
consistent interfaces for all approaches.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from enum import Enum

from ..core.clients import config, typesense_client
from ..models.schemas import QuestionRequest

# Import available search strategies
from ..services.classification_service import classify_question
from ..services.unified_search_service import unified_search

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Available search strategies"""

    CLASSIFICATION = "classification"
    UNIFIED = "unified"


class SmartSearchRouter:
    """Intelligent search router that selects optimal strategy"""

    def __init__(self):
        self.config = config
        self.client = typesense_client

        # Get configured search strategy
        strategy_name = self.config.hybrid_search.search_strategy.lower()
        try:
            self.current_strategy = SearchStrategy(strategy_name)
        except ValueError:
            logger.warning(
                f"Invalid search strategy '{strategy_name}', defaulting to unified"
            )
            self.current_strategy = SearchStrategy.UNIFIED

        logger.info(
            f"Search router initialized with strategy: {self.current_strategy.value}"
        )

        # Performance tracking
        self.performance_stats = {
            "classification": {"total_calls": 0, "total_time": 0.0, "avg_results": 0.0},
            "unified": {"total_calls": 0, "total_time": 0.0, "avg_results": 0.0},
        }

    async def search(
        self, payload: QuestionRequest, force_strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route search request to the appropriate strategy

        Args:
            payload: Question request
            force_strategy: Override configured strategy (for testing)

        Returns:
            Standardized search response with metadata
        """
        start_time = time.time()

        # Determine which strategy to use
        if force_strategy:
            try:
                strategy = SearchStrategy(force_strategy.lower())
            except ValueError:
                logger.warning(
                    f"Invalid force_strategy '{force_strategy}', using configured strategy"
                )
                strategy = self.current_strategy
        else:
            strategy = self.current_strategy

        logger.info(
            f"Routing search with {strategy.value} strategy: '{payload.question[:50]}...'"
        )

        try:
            # Route to appropriate search method
            if strategy == SearchStrategy.CLASSIFICATION:
                results = await self._classification_search(payload)
            elif strategy == SearchStrategy.UNIFIED:
                results = await self._unified_search(payload)
            else:
                raise ValueError(f"Unknown search strategy: {strategy}")

            search_time = time.time() - start_time

            # Update performance stats
            strategy_name = strategy.value
            self.performance_stats[strategy_name]["total_calls"] += 1
            self.performance_stats[strategy_name]["total_time"] += search_time
            self.performance_stats[strategy_name]["avg_results"] = (
                self.performance_stats[strategy_name]["avg_results"]
                * (self.performance_stats[strategy_name]["total_calls"] - 1)
                + len(results)
            ) / self.performance_stats[strategy_name]["total_calls"]

            # Prepare response with metadata
            response = {
                "results": results,
                "metadata": {
                    "strategy_used": strategy.value,
                    "search_time": round(search_time, 3),
                    "result_count": len(results),
                    "question": payload.question,
                    "timestamp": time.time(),
                },
            }

            logger.info(
                f"Search completed: {len(results)} results in {search_time:.3f}s using {strategy.value}"
            )
            return response

        except Exception as e:
            logger.error(f"Search failed with {strategy.value} strategy: {e}")

            # Fallback to unified search if other strategies fail
            if strategy != SearchStrategy.UNIFIED:
                logger.info("Falling back to unified search strategy")
                return await self.search(payload, force_strategy="unified")
            else:
                # If unified search fails, return empty results
                return {
                    "results": [],
                    "metadata": {
                        "strategy_used": strategy.value,
                        "search_time": time.time() - start_time,
                        "result_count": 0,
                        "error": str(e),
                        "question": payload.question,
                        "timestamp": time.time(),
                    },
                }

    async def _classification_search(
        self, payload: QuestionRequest
    ) -> List[Dict[str, Any]]:
        """Execute classification-based search"""
        if not self.config.hybrid_search.strategies.classification.enabled:
            raise ValueError("Classification search is disabled in configuration")

        # Step 1: Classify question to get relevant collections
        classification_result = await classify_question(payload)
        collections = classification_result.get("collections", [])

        if not collections:
            # Use fallback collections if classification returns nothing
            collections = (
                self.config.hybrid_search.strategies.classification.fallback_collections
            )
            logger.warning(
                f"Classification returned no collections, using fallback: {collections}"
            )

        # Step 2: Search the classified collections
        return await self._search_collections(payload.question, collections)

    async def _enhanced_search(self, payload: QuestionRequest) -> List[Dict[str, Any]]:
        """Execute enhanced keyword-based search"""
        if not self.config.hybrid_search.strategies.enhanced.enabled:
            raise ValueError("Enhanced search is disabled in configuration")

        return await enhanced_search(payload, use_fallback=True)

    async def _unified_search(self, payload: QuestionRequest) -> List[Dict[str, Any]]:
        """Execute unified knowledge base search"""
        if not self.config.hybrid_search.strategies.unified.enabled:
            raise ValueError("Unified search is disabled in configuration")

        max_results = getattr(
            self.config.hybrid_search.strategies.unified,
            "max_results",
            self.config.hybrid_search.top_k,
        )
        return await unified_search(payload, max_results=max_results)

    async def _search_collections(
        self, question: str, collections: List[str]
    ) -> List[Dict[str, Any]]:
        """Helper method to search specific collections (used by classification strategy)"""
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

                    if "vector_distance" in hit:
                        result["vector_distance"] = hit["vector_distance"]

                    all_results.append(result)

                logger.debug(
                    f"Found {len(results.get('hits', []))} results in {collection_name}"
                )

            except Exception as e:
                logger.error(f"Error searching collection {collection_name}: {e}")
                continue

        # Sort by relevance and limit results
        sorted_results = sorted(
            all_results, key=lambda x: x.get("text_match", 0), reverse=True
        )

        return sorted_results[: self.config.hybrid_search.top_k]

    async def compare_strategies(self, payload: QuestionRequest) -> Dict[str, Any]:
        """
        Compare all enabled strategies for the same question
        Useful for performance analysis and strategy optimization
        """
        comparison_results = {
            "question": payload.question,
            "strategies": {},
            "recommendation": None,
        }

        enabled_strategies = []
        if self.config.hybrid_search.strategies.classification.enabled:
            enabled_strategies.append(SearchStrategy.CLASSIFICATION)
        if self.config.hybrid_search.strategies.enhanced.enabled:
            enabled_strategies.append(SearchStrategy.ENHANCED)
        if self.config.hybrid_search.strategies.unified.enabled:
            enabled_strategies.append(SearchStrategy.UNIFIED)

        for strategy in enabled_strategies:
            try:
                start_time = time.time()
                response = await self.search(payload, force_strategy=strategy.value)

                comparison_results["strategies"][strategy.value] = {
                    "results": response["results"],
                    "metadata": response["metadata"],
                    "performance": {
                        "response_time": response["metadata"]["search_time"],
                        "result_count": response["metadata"]["result_count"],
                    },
                }

            except Exception as e:
                comparison_results["strategies"][strategy.value] = {
                    "error": str(e),
                    "performance": {"response_time": None, "result_count": 0},
                }

        # Generate recommendation based on performance and results
        best_strategy = self._recommend_strategy(comparison_results["strategies"])
        comparison_results["recommendation"] = best_strategy

        return comparison_results

    def _recommend_strategy(self, strategy_results: Dict) -> str:
        """Recommend the best strategy based on performance and quality"""
        scores = {}

        for strategy_name, data in strategy_results.items():
            if "error" in data:
                scores[strategy_name] = 0
                continue

            perf = data["performance"]
            response_time = perf.get("response_time", 999)
            result_count = perf.get("result_count", 0)

            # Score based on speed (lower is better) and result count (higher is better)
            # Normalize scores: speed score inversely related to time, result score directly related to count
            speed_score = max(0, 1 - (response_time / 5.0))  # Normalize to 5 second max
            result_score = min(result_count / 10.0, 1.0)  # Normalize to 10 results max

            # Weighted combination (speed is more important for user experience)
            scores[strategy_name] = 0.7 * speed_score + 0.3 * result_score

        if not scores:
            return "unified"  # Default fallback

        return max(scores, key=scores.get)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all strategies"""
        stats = {
            "current_strategy": self.current_strategy.value,
            "performance_by_strategy": {},
        }

        for strategy_name, data in self.performance_stats.items():
            if data["total_calls"] > 0:
                avg_time = data["total_time"] / data["total_calls"]
                stats["performance_by_strategy"][strategy_name] = {
                    "total_calls": data["total_calls"],
                    "average_response_time": round(avg_time, 3),
                    "average_results": round(data["avg_results"], 1),
                    "total_time": round(data["total_time"], 3),
                }
            else:
                stats["performance_by_strategy"][strategy_name] = {
                    "total_calls": 0,
                    "average_response_time": 0,
                    "average_results": 0,
                    "total_time": 0,
                }

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all search strategies and collections"""
        health_status = {
            "overall_status": "healthy",
            "strategies": {},
            "collections": {},
            "timestamp": time.time(),
        }

        # Check strategy availability
        for strategy in SearchStrategy:
            strategy_name = strategy.value
            config_path = f"strategies.{strategy_name}"

            try:
                strategy_config = getattr(
                    self.config.hybrid_search, config_path.split(".")[0], None
                )
                if strategy_config and hasattr(strategy_config, strategy_name):
                    enabled = getattr(
                        getattr(strategy_config, strategy_name), "enabled", False
                    )
                    health_status["strategies"][strategy_name] = {
                        "enabled": enabled,
                        "status": "available" if enabled else "disabled",
                    }
                else:
                    health_status["strategies"][strategy_name] = {
                        "enabled": False,
                        "status": "not_configured",
                    }
            except Exception as e:
                health_status["strategies"][strategy_name] = {
                    "enabled": False,
                    "status": "error",
                    "error": str(e),
                }

        # Check key collections
        key_collections = [
            "unified_knowledge_base",
            "discourse_posts_optimized",
            "chapters_misc",
        ]

        for collection in key_collections:
            try:
                schema = self.client.collections[collection].retrieve()
                doc_count = schema.get("num_documents", 0)
                health_status["collections"][collection] = {
                    "status": "healthy" if doc_count > 0 else "empty",
                    "document_count": doc_count,
                }
            except Exception as e:
                health_status["collections"][collection] = {
                    "status": "error",
                    "error": str(e),
                }

        # Determine overall status
        strategy_errors = sum(
            1
            for s in health_status["strategies"].values()
            if s.get("status") == "error"
        )
        collection_errors = sum(
            1
            for c in health_status["collections"].values()
            if c.get("status") == "error"
        )

        if strategy_errors > 0 or collection_errors > 0:
            health_status["overall_status"] = "degraded"

        return health_status


# Create global instance
smart_search_router = SmartSearchRouter()


# ******************** convenience functions ********************#
async def smart_search(
    payload: QuestionRequest, force_strategy: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for smart search routing"""
    return await smart_search_router.search(payload, force_strategy)


async def compare_search_strategies(payload: QuestionRequest) -> Dict[str, Any]:
    """Compare all enabled search strategies for a question"""
    return await smart_search_router.compare_strategies(payload)


async def get_search_performance_stats() -> Dict[str, Any]:
    """Get performance statistics for all search strategies"""
    return smart_search_router.get_performance_stats()


async def search_health_check() -> Dict[str, Any]:
    """Perform health check on search system"""
    return await smart_search_router.health_check()
