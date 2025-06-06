#!/usr/bin/env python3
"""
Performance Comparison Script for Teaching Assistant Search Strategies

This script compares:
1. Classification-based search (current approach)
2. Direct unified knowledge base search
3. Optimized search for discourse posts and misc collections

It measures:
- Response time
- Search accuracy (number of relevant results)
- Answer quality (based on result relevance)
"""

import time
import json
import asyncio
import statistics
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Add project root to path
import sys

sys.path.append(str(Path(__file__).parent))

from lib.config import get_config, get_typesense_client, get_openai_client
from api.services.classification_service import classify_question
from api.services.search_service import hybrid_search_across_collections
from api.models.schemas import QuestionRequest


class SearchPerformanceComparator:
    def __init__(self):
        self.config = get_config()
        self.typesense_client = get_typesense_client()
        self.openai_client = get_openai_client()

        # Test questions covering different domains
        self.test_questions = [
            # Data sourcing questions
            "How to scrape data from websites using Python?",
            "What is web scraping and how does it work?",
            "How to use APIs for data collection?",
            # LLM questions
            "How does LLM extraction work?",
            "What is prompt engineering?",
            "How to use embeddings for semantic search?",
            # Development tools
            "How to use Docker for development?",
            "What is Git and how to use it?",
            "How to set up VSCode for Python development?",
            # Discourse/QA type questions
            "I'm having trouble with my project submission",
            "Can someone help me debug this error?",
            "What are the assignment requirements?",
            # General course questions
            "What tools are covered in this course?",
            "How to prepare data for analysis?",
            "What visualization tools should I use?",
        ]

    async def classification_based_search(
        self, question: str
    ) -> Tuple[List[Dict], float]:
        """Current classification-based approach"""
        start_time = time.time()

        # Step 1: Classify question
        question_request = QuestionRequest(question=question)
        classification_result = await classify_question(question_request)
        collections = classification_result.get("collections", [])

        # Step 2: Search classified collections
        all_results = []
        search_params = {
            "q": question,
            "query_by": "content",
            "per_page": self.config.hybrid_search.top_k,
            "num_typos": self.config.hybrid_search.num_typos,
        }

        for collection in collections:
            try:
                results = self.typesense_client.collections[
                    collection
                ].documents.search(search_params)
                for hit in results.get("hits", []):
                    hit_with_collection = dict(hit)
                    hit_with_collection["collection"] = collection
                    all_results.append(hit_with_collection)
            except Exception as e:
                print(f"Error searching collection {collection}: {e}")

        end_time = time.time()
        return all_results, end_time - start_time

    async def direct_unified_search(self, question: str) -> Tuple[List[Dict], float]:
        """Direct search on unified knowledge base"""
        start_time = time.time()

        search_params = {
            "q": question,
            "query_by": "content",
            "per_page": self.config.hybrid_search.top_k
            * 2,  # Get more results since no classification
            "num_typos": self.config.hybrid_search.num_typos,
        }

        try:
            results = self.typesense_client.collections[
                "unified_knowledge_base"
            ].documents.search(search_params)
            all_results = []
            for hit in results.get("hits", []):
                hit_with_collection = dict(hit)
                hit_with_collection["collection"] = "unified_knowledge_base"
                all_results.append(hit_with_collection)
        except Exception as e:
            print(f"Error searching unified knowledge base: {e}")
            all_results = []

        end_time = time.time()
        return all_results, end_time - start_time

    async def optimized_discourse_misc_search(
        self, question: str
    ) -> Tuple[List[Dict], float]:
        """Optimized search focusing on discourse posts and misc collections"""
        start_time = time.time()

        # Priority collections for student Q&A and live sessions
        priority_collections = [
            "discourse_posts_optimized",
            "chapters_misc",
        ]

        # Additional collections based on keyword detection
        keyword_collections = {
            "scraping": ["chapters_data_sourcing"],
            "docker": ["chapters_development_tools", "chapters_deployment_tools"],
            "git": ["chapters_development_tools"],
            "llm": ["chapters_large_language_models"],
            "embedding": ["chapters_large_language_models"],
            "visualization": ["chapters_data_visualization"],
            "analysis": ["chapters_data_analysis"],
            "preparation": ["chapters_data_preparation"],
        }

        collections_to_search = priority_collections.copy()

        # Add collections based on keywords
        question_lower = question.lower()
        for keyword, cols in keyword_collections.items():
            if keyword in question_lower:
                collections_to_search.extend(cols)

        # Remove duplicates while preserving order
        collections_to_search = list(dict.fromkeys(collections_to_search))

        all_results = []
        search_params = {
            "q": question,
            "query_by": "content",
            "per_page": self.config.hybrid_search.top_k,
            "num_typos": self.config.hybrid_search.num_typos,
        }

        for collection in collections_to_search:
            try:
                results = self.typesense_client.collections[
                    collection
                ].documents.search(search_params)
                for hit in results.get("hits", []):
                    hit_with_collection = dict(hit)
                    hit_with_collection["collection"] = collection
                    all_results.append(hit_with_collection)
            except Exception as e:
                print(f"Error searching collection {collection}: {e}")

        end_time = time.time()
        return all_results, end_time - start_time

    def evaluate_results(self, results: List[Dict], question: str) -> Dict[str, Any]:
        """Evaluate search results quality"""
        if not results:
            return {
                "num_results": 0,
                "avg_score": 0,
                "max_score": 0,
                "collections_covered": 0,
                "has_discourse": False,
                "has_misc": False,
            }

        scores = []
        collections = set()
        has_discourse = False
        has_misc = False

        for result in results:
            # Get search score (higher is better in Typesense)
            score = result.get("text_match", 0)
            scores.append(score)

            collection = result.get("collection", "")
            collections.add(collection)

            if "discourse" in collection:
                has_discourse = True
            if "misc" in collection:
                has_misc = True

        return {
            "num_results": len(results),
            "avg_score": statistics.mean(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "collections_covered": len(collections),
            "has_discourse": has_discourse,
            "has_misc": has_misc,
            "collections": list(collections),
        }

    async def run_comparison(self) -> Dict[str, Any]:
        """Run comprehensive performance comparison"""
        print("=== Teaching Assistant Search Performance Comparison ===\n")

        results = {
            "classification_based": {"times": [], "evaluations": []},
            "direct_unified": {"times": [], "evaluations": []},
            "optimized_discourse_misc": {"times": [], "evaluations": []},
        }

        for i, question in enumerate(self.test_questions, 1):
            print(
                f"Testing question {i}/{len(self.test_questions)}: {question[:50]}..."
            )

            # Test classification-based search
            try:
                search_results, search_time = await self.classification_based_search(
                    question
                )
                evaluation = self.evaluate_results(search_results, question)
                results["classification_based"]["times"].append(search_time)
                results["classification_based"]["evaluations"].append(evaluation)
                print(
                    f"  Classification-based: {len(search_results)} results in {search_time:.3f}s"
                )
            except Exception as e:
                print(f"  Classification-based error: {e}")
                results["classification_based"]["times"].append(999)
                results["classification_based"]["evaluations"].append(
                    self.evaluate_results([], question)
                )

            # Test direct unified search
            try:
                search_results, search_time = await self.direct_unified_search(question)
                evaluation = self.evaluate_results(search_results, question)
                results["direct_unified"]["times"].append(search_time)
                results["direct_unified"]["evaluations"].append(evaluation)
                print(
                    f"  Direct unified: {len(search_results)} results in {search_time:.3f}s"
                )
            except Exception as e:
                print(f"  Direct unified error: {e}")
                results["direct_unified"]["times"].append(999)
                results["direct_unified"]["evaluations"].append(
                    self.evaluate_results([], question)
                )

            # Test optimized discourse/misc search
            try:
                search_results, search_time = (
                    await self.optimized_discourse_misc_search(question)
                )
                evaluation = self.evaluate_results(search_results, question)
                results["optimized_discourse_misc"]["times"].append(search_time)
                results["optimized_discourse_misc"]["evaluations"].append(evaluation)
                print(
                    f"  Optimized discourse/misc: {len(search_results)} results in {search_time:.3f}s"
                )
            except Exception as e:
                print(f"  Optimized discourse/misc error: {e}")
                results["optimized_discourse_misc"]["times"].append(999)
                results["optimized_discourse_misc"]["evaluations"].append(
                    self.evaluate_results([], question)
                )

            print()  # Empty line for readability

        return results

    def analyze_results(self, results: Dict[str, Any]) -> None:
        """Analyze and display performance comparison results"""
        print("\n=== PERFORMANCE ANALYSIS ===\n")

        for approach, data in results.items():
            print(f"--- {approach.replace('_', ' ').title()} ---")

            times = [t for t in data["times"] if t < 999]  # Exclude error times
            evaluations = data["evaluations"]

            if times:
                print(f"Average response time: {statistics.mean(times):.3f}s")
                print(f"Median response time: {statistics.median(times):.3f}s")
                print(f"Min/Max response time: {min(times):.3f}s / {max(times):.3f}s")

            # Result quality analysis
            num_results = [e["num_results"] for e in evaluations]
            avg_scores = [e["avg_score"] for e in evaluations if e["avg_score"] > 0]
            collections_covered = [e["collections_covered"] for e in evaluations]
            discourse_coverage = sum(1 for e in evaluations if e["has_discourse"])
            misc_coverage = sum(1 for e in evaluations if e["has_misc"])

            print(f"Average results per query: {statistics.mean(num_results):.1f}")
            print(
                f"Average search score: {statistics.mean(avg_scores):.2f}"
                if avg_scores
                else "No valid scores"
            )
            print(
                f"Average collections covered: {statistics.mean(collections_covered):.1f}"
            )
            print(
                f"Discourse coverage: {discourse_coverage}/{len(self.test_questions)} queries ({discourse_coverage/len(self.test_questions)*100:.1f}%)"
            )
            print(
                f"Misc coverage: {misc_coverage}/{len(self.test_questions)} queries ({misc_coverage/len(self.test_questions)*100:.1f}%)"
            )
            print()

    def save_detailed_results(
        self, results: Dict[str, Any], filename: str = "search_performance_results.json"
    ) -> None:
        """Save detailed results to JSON file"""
        detailed_results = {
            "test_questions": self.test_questions,
            "results": results,
            "config": {
                "top_k": self.config.hybrid_search.top_k,
                "num_typos": self.config.hybrid_search.num_typos,
                "alpha": self.config.hybrid_search.alpha,
            },
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)

        print(f"Detailed results saved to {filename}")


async def main():
    """Main function to run the performance comparison"""
    comparator = SearchPerformanceComparator()

    try:
        results = await comparator.run_comparison()
        comparator.analyze_results(results)
        comparator.save_detailed_results(results)

        print("\n=== RECOMMENDATIONS ===")
        print("Based on the performance analysis:")
        print("1. Compare response times across approaches")
        print("2. Evaluate result quality and relevance")
        print("3. Consider hybrid approach combining best of all methods")
        print("4. Optimize for specific question types (discourse vs technical)")

    except Exception as e:
        print(f"Error during comparison: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
