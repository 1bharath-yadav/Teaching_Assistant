#!/usr/bin/env python3
"""
Optimized Search Service for Teaching Assistant

This service implements intelligent search strategy selection based on question type:
1. Student Q&A questions → Priority to discourse posts
2. Live session questions → Priority to misc collection
3. Technical questions → Classification-based search
4. General questions → Unified knowledge base search

Features:
- Question type detection
- Dynamic collection prioritization
- Fallback strategies
- Performance optimization
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from lib.config import get_config, get_typesense_client
from api.services.classification_service import classify_question


class QuestionType(Enum):
    STUDENT_QA = "student_qa"  # Questions about assignments, projects, issues
    LIVE_SESSION = "live_session"  # Questions from live sessions, general help
    TECHNICAL = "technical"  # Specific technical questions about tools/concepts
    GENERAL = "general"  # General course questions


@dataclass
class SearchResult:
    """Standardized search result structure"""

    content: str
    score: float
    collection: str
    metadata: Dict[str, Any]
    document_id: str


@dataclass
class SearchStrategy:
    """Search strategy configuration"""

    primary_collections: List[str]
    secondary_collections: List[str]
    search_params: Dict[str, Any]
    fallback_to_unified: bool = True


class OptimizedSearchService:
    def __init__(self):
        self.config = get_config()
        self.typesense_client = get_typesense_client()

        # Question type detection patterns
        self.qa_patterns = [
            r"help.*with.*project",
            r"having.*trouble",
            r"error.*in.*assignment",
            r"can.*someone.*help",
            r"how.*to.*submit",
            r"assignment.*requirements",
            r"project.*submission",
            r"deadline.*for",
            r"what.*should.*i.*do",
            r"i.*don\'t.*understand",
            r"confused.*about",
            r"stuck.*on",
        ]

        self.live_session_patterns = [
            r"live.*session",
            r"class.*question",
            r"during.*lecture",
            r"professor.*said",
            r"in.*today\'s.*class",
            r"from.*the.*session",
            r"discussed.*in.*class",
            r"what.*was.*covered",
        ]

        self.technical_patterns = [
            r"how.*does.*\w+.*work",
            r"what.*is.*\w+",
            r"how.*to.*use.*\w+",
            r"implement.*\w+",
            r"configure.*\w+",
            r"install.*\w+",
        ]

        # Collection mappings
        self.collection_mapping = {
            "data_sourcing": "chapters_data_sourcing",
            "data_preparation": "chapters_data_preparation",
            "data_analysis": "chapters_data_analysis",
            "data_visualization": "chapters_data_visualization",
            "llm": "chapters_large_language_models",
            "development_tools": "chapters_development_tools",
            "deployment_tools": "chapters_deployment_tools",
            "misc": "chapters_misc",
            "discourse": "discourse_posts_optimized",
        }

    def detect_question_type(self, question: str) -> QuestionType:
        """Detect the type of question to determine optimal search strategy"""
        question_lower = question.lower()

        # Check for student Q&A patterns
        for pattern in self.qa_patterns:
            if re.search(pattern, question_lower):
                return QuestionType.STUDENT_QA

        # Check for live session patterns
        for pattern in self.live_session_patterns:
            if re.search(pattern, question_lower):
                return QuestionType.LIVE_SESSION

        # Check for technical patterns
        for pattern in self.technical_patterns:
            if re.search(pattern, question_lower):
                return QuestionType.TECHNICAL

        # Default to general
        return QuestionType.GENERAL

    def get_search_strategy(
        self, question: str, question_type: QuestionType
    ) -> SearchStrategy:
        """Get optimized search strategy based on question type"""

        if question_type == QuestionType.STUDENT_QA:
            return SearchStrategy(
                primary_collections=["discourse_posts_optimized"],
                secondary_collections=["chapters_misc", "unified_knowledge_base"],
                search_params={
                    "per_page": 8,
                    "num_typos": 3,
                    "query_by": "content,topic_title",
                    "prioritize_exact_match": True,
                },
            )

        elif question_type == QuestionType.LIVE_SESSION:
            return SearchStrategy(
                primary_collections=["chapters_misc"],
                secondary_collections=[
                    "discourse_posts_optimized",
                    "unified_knowledge_base",
                ],
                search_params={
                    "per_page": 6,
                    "num_typos": 2,
                    "query_by": "content",
                    "prioritize_exact_match": True,
                },
            )

        elif question_type == QuestionType.TECHNICAL:
            # Use classification for technical questions
            return SearchStrategy(
                primary_collections=[],  # Will be populated by classification
                secondary_collections=["unified_knowledge_base"],
                search_params={
                    "per_page": 5,
                    "num_typos": 2,
                    "query_by": "content",
                },
            )

        else:  # GENERAL
            return SearchStrategy(
                primary_collections=["unified_knowledge_base"],
                secondary_collections=["discourse_posts_optimized", "chapters_misc"],
                search_params={
                    "per_page": 10,
                    "num_typos": 3,
                    "query_by": "content",
                },
            )

    async def search_collection(
        self, collection: str, question: str, params: Dict[str, Any]
    ) -> List[SearchResult]:
        """Search a single collection and return standardized results"""
        search_params = {"q": question, **params}

        try:
            response = self.typesense_client.collections[collection].search(
                search_params
            )
            results = []

            for hit in response.get("hits", []):
                doc = hit.get("document", {})
                result = SearchResult(
                    content=doc.get("content", ""),
                    score=hit.get("text_match", 0),
                    collection=collection,
                    metadata=doc,
                    document_id=doc.get("id", ""),
                )
                results.append(result)

            return results

        except Exception as e:
            print(f"Error searching collection {collection}: {e}")
            return []

    async def execute_search_strategy(
        self, question: str, strategy: SearchStrategy
    ) -> List[SearchResult]:
        """Execute the search strategy and return combined results"""
        all_results = []

        # Handle technical questions with classification
        collections_to_search = strategy.primary_collections
        if (
            not collections_to_search and strategy.search_params.get("per_page") == 5
        ):  # Technical question
            try:
                classification_result = await classify_question({"question": question})
                collections_to_search = classification_result.get("collections", [])
            except Exception as e:
                print(f"Classification error: {e}")
                collections_to_search = strategy.secondary_collections[:2]

        # Search primary collections
        for collection in collections_to_search:
            results = await self.search_collection(
                collection, question, strategy.search_params
            )
            all_results.extend(results)

        # If insufficient results, search secondary collections
        if len(all_results) < strategy.search_params.get("per_page", 5) // 2:
            for collection in strategy.secondary_collections:
                if collection not in collections_to_search:
                    results = await self.search_collection(
                        collection, question, strategy.search_params
                    )
                    all_results.extend(results)

                    # Stop if we have enough results
                    if len(all_results) >= strategy.search_params.get("per_page", 5):
                        break

        # Sort by score (descending)
        all_results.sort(key=lambda x: x.score, reverse=True)

        # Limit to requested number of results
        max_results = strategy.search_params.get("per_page", 5)
        return all_results[:max_results]

    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content similarity"""
        if not results:
            return results

        unique_results = []
        seen_content = set()

        for result in results:
            # Simple deduplication based on first 100 characters
            content_key = result.content[:100].strip().lower()
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)

        return unique_results

    def enhance_results_for_discourse(
        self, results: List[SearchResult]
    ) -> List[SearchResult]:
        """Enhance discourse post results with additional context"""
        enhanced_results = []

        for result in results:
            if result.collection == "discourse_posts_optimized":
                # Add topic title to content for better context
                topic_title = result.metadata.get("topic_title", "")
                if topic_title and topic_title not in result.content:
                    result.content = f"**{topic_title}**\n\n{result.content}"

            enhanced_results.append(result)

        return enhanced_results

    async def optimized_search(
        self, question: str
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """Main optimized search function"""
        start_time = time.time()

        # Step 1: Detect question type
        question_type = self.detect_question_type(question)

        # Step 2: Get search strategy
        strategy = self.get_search_strategy(question, question_type)

        # Step 3: Execute search
        results = await self.execute_search_strategy(question, strategy)

        # Step 4: Post-process results
        results = self.deduplicate_results(results)
        results = self.enhance_results_for_discourse(results)

        end_time = time.time()

        # Metadata about the search
        search_metadata = {
            "question_type": question_type.value,
            "search_time": end_time - start_time,
            "num_results": len(results),
            "collections_searched": list(set(r.collection for r in results)),
            "strategy_used": {
                "primary_collections": strategy.primary_collections,
                "secondary_collections": strategy.secondary_collections,
            },
        }

        return results, search_metadata

    def format_results_for_api(
        self, results: List[SearchResult]
    ) -> List[Dict[str, Any]]:
        """Format results for API response"""
        formatted_results = []

        for result in results:
            formatted_result = {
                "content": result.content,
                "score": result.score,
                "collection": result.collection,
                "document_id": result.document_id,
                "metadata": {
                    "title": result.metadata.get(
                        "topic_title", result.metadata.get("title", "")
                    ),
                    "url": result.metadata.get("url", ""),
                    "timestamp": result.metadata.get("timestamp", ""),
                },
            }
            formatted_results.append(formatted_result)

        return formatted_results


# Global service instance
_optimized_search_service = None


def get_optimized_search_service() -> OptimizedSearchService:
    """Get the global optimized search service instance"""
    global _optimized_search_service
    if _optimized_search_service is None:
        _optimized_search_service = OptimizedSearchService()
    return _optimized_search_service


# Convenience function for direct use
async def optimized_search(
    question: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Convenience function for optimized search"""
    service = get_optimized_search_service()
    results, metadata = await service.optimized_search(question)
    formatted_results = service.format_results_for_api(results)
    return formatted_results, metadata
