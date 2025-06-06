#!/usr/bin/env python3
"""
Comprehensive Test Script for Typesense Hybrid Search and Multi-Search

This script demonstrates various search capabilities based on official Typesense documentation:
- Hybrid Search (keyword + vector)
- Semantic Search (pure vector)
- Federated Search (multiple collections)
- Union Search (merged results)
- Advanced filtering and ranking
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "data"))

from optimized_rag_pipeline import OptimizedRAGPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("hybrid_search_test.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SearchTester:
    """Comprehensive search testing class."""

    def __init__(self):
        """Initialize the search tester."""
        self.pipeline = OptimizedRAGPipeline()
        self.test_results = []
        self.output_dir = current_dir / "search_test_results"
        self.output_dir.mkdir(exist_ok=True)

    def run_search_type_comparison(self, query: str) -> Dict:
        """Compare different search types for the same query."""
        logger.info(f"Running search type comparison for: '{query}'")

        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "search_types": {},
        }

        # 1. Pure keyword search (no vector)
        logger.info("Testing pure keyword search...")
        try:
            keyword_response = self.pipeline.client.multi_search.perform(
                {
                    "searches": [
                        {
                            "collection": "unified_knowledge_base",
                            "q": query,
                            "query_by": "content,clean_content",
                            "exclude_fields": "embedding",
                            "per_page": 5,
                        }
                    ]
                }
            )
            results["search_types"]["keyword_only"] = (
                self.pipeline._parse_search_response(keyword_response, "keyword")
            )
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            results["search_types"]["keyword_only"] = []

        # 2. Pure semantic search
        logger.info("Testing pure semantic search...")
        results["search_types"]["semantic_only"] = self.pipeline.test_semantic_search(
            query
        )

        # 3. Hybrid search with different alpha values
        alpha_values = [0.1, 0.3, 0.5, 0.7, 0.9]
        results["search_types"]["hybrid_alpha_comparison"] = {}

        for alpha in alpha_values:
            logger.info(f"Testing hybrid search with alpha={alpha}...")
            results["search_types"]["hybrid_alpha_comparison"][f"alpha_{alpha}"] = (
                self.pipeline.test_hybrid_search(query, alpha=alpha)
            )

        return results

    def test_advanced_features(self, query: str) -> Dict:
        """Test advanced search features."""
        logger.info(f"Testing advanced features for: '{query}'")

        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "advanced_features": {},
        }

        # 1. Distance threshold testing
        distance_thresholds = [0.3, 0.5, 0.7, 0.9]
        results["advanced_features"]["distance_threshold"] = {}

        for threshold in distance_thresholds:
            logger.info(f"Testing distance threshold: {threshold}")
            results["advanced_features"]["distance_threshold"][
                f"threshold_{threshold}"
            ] = self.pipeline.test_advanced_hybrid_search(
                query, distance_threshold=threshold, alpha=0.7
            )

        # 2. Different sorting methods
        sort_methods = [
            "_text_match:desc",
            "_vector_distance:asc",
            "content_length:desc",
            "_text_match:desc,_vector_distance:asc",
        ]
        results["advanced_features"]["sorting"] = {}

        for sort_by in sort_methods:
            logger.info(f"Testing sort method: {sort_by}")
            results["advanced_features"]["sorting"][
                sort_by.replace(":", "_").replace(",", "_")
            ] = self.pipeline.test_advanced_hybrid_search(
                query, sort_by=sort_by, alpha=0.7
            )

        # 3. Filtering tests
        filters = [
            "has_code:true",
            "content_length:>100",
            "source_type:discourse",
            "source_type:chapters",
        ]
        results["advanced_features"]["filtering"] = {}

        for filter_by in filters:
            logger.info(f"Testing filter: {filter_by}")
            results["advanced_features"]["filtering"][
                filter_by.replace(":", "_").replace(">", "gt")
            ] = self.pipeline.test_advanced_hybrid_search(
                query, filters=filter_by, alpha=0.7
            )

        return results

    def test_federated_capabilities(self, query: str) -> Dict:
        """Test federated and union search capabilities."""
        logger.info(f"Testing federated capabilities for: '{query}'")

        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "federated_tests": {},
        }

        # Get available collections
        try:
            collections_response = self.pipeline.client.collections.retrieve()
            available_collections = [col["name"] for col in collections_response]
            logger.info(f"Available collections: {available_collections}")
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            available_collections = ["unified_knowledge_base"]

        # 1. Federated search across collections
        logger.info("Testing federated search...")
        results["federated_tests"]["federated"] = self.pipeline.test_federated_search(
            query, collections=available_collections[:3]  # Limit to 3 collections
        )

        # 2. Union search
        logger.info("Testing union search...")
        results["federated_tests"]["union"] = self.pipeline.test_union_search(
            query, collections=available_collections[:2]  # Limit to 2 collections
        )

        return results

    def performance_comparison(self, queries: List[str]) -> Dict:
        """Compare performance across different search methods."""
        logger.info("Running performance comparison...")

        results = {"timestamp": datetime.now().isoformat(), "performance_tests": {}}

        for query in queries:
            logger.info(f"Performance testing query: '{query}'")

            query_results = {"query": query, "timing": {}}

            # Time different search methods
            import time

            methods = [
                ("hybrid_search", lambda: self.pipeline.test_hybrid_search(query)),
                ("semantic_search", lambda: self.pipeline.test_semantic_search(query)),
                (
                    "advanced_hybrid",
                    lambda: self.pipeline.test_advanced_hybrid_search(query),
                ),
            ]

            for method_name, method_func in methods:
                start_time = time.time()
                try:
                    method_results = method_func()
                    end_time = time.time()

                    query_results["timing"][method_name] = {
                        "duration_seconds": end_time - start_time,
                        "results_count": len(method_results),
                        "success": True,
                    }
                except Exception as e:
                    end_time = time.time()
                    query_results["timing"][method_name] = {
                        "duration_seconds": end_time - start_time,
                        "results_count": 0,
                        "success": False,
                        "error": str(e),
                    }

            results["performance_tests"][query.replace(" ", "_")] = query_results

        return results

    def run_comprehensive_test_suite(self):
        """Run the complete test suite."""
        logger.info("Starting comprehensive search test suite...")
        logger.info("=" * 70)

        test_queries = [
            "machine learning algorithms",
            "data visualization with python",
            "deployment best practices",
            "data preprocessing techniques",
            "statistical analysis methods",
        ]

        all_results = {
            "test_suite": "Comprehensive Typesense Search Testing",
            "timestamp": datetime.now().isoformat(),
            "queries_tested": test_queries,
            "results": {},
        }

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n[{i}/{len(test_queries)}] Testing query: '{query}'")
            logger.info("-" * 50)

            # 1. Search type comparison
            search_comparison = self.run_search_type_comparison(query)

            # 2. Advanced features testing
            advanced_features = self.test_advanced_features(query)

            # 3. Federated capabilities (only for first query to avoid overload)
            if i == 1:
                federated_tests = self.test_federated_capabilities(query)
            else:
                federated_tests = {"note": "Federated tests run only for first query"}

            all_results["results"][query] = {
                "search_comparison": search_comparison,
                "advanced_features": advanced_features,
                "federated_tests": federated_tests,
            }

        # 4. Performance comparison
        logger.info("\nRunning performance comparison...")
        performance_results = self.performance_comparison(
            test_queries[:3]
        )  # Limit for performance
        all_results["performance_comparison"] = performance_results

        # Save comprehensive results
        output_file = (
            self.output_dir
            / f"comprehensive_search_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        logger.info(f"\nComprehensive test results saved to: {output_file}")
        logger.info("=" * 70)

        # Generate summary report
        self.generate_summary_report(
            all_results, output_file.parent / "test_summary.txt"
        )

        return all_results

    def generate_summary_report(self, results: Dict, output_file: Path):
        """Generate a human-readable summary report."""
        logger.info("Generating summary report...")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("TYPESENSE HYBRID & MULTI-SEARCH TEST SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Test Date: {results['timestamp']}\n")
            f.write(f"Queries Tested: {len(results['queries_tested'])}\n\n")

            # Performance summary
            if "performance_comparison" in results:
                f.write("PERFORMANCE SUMMARY\n")
                f.write("-" * 20 + "\n")

                for query, perf_data in results["performance_comparison"][
                    "performance_tests"
                ].items():
                    f.write(f"\nQuery: {query}\n")
                    for method, timing in perf_data["timing"].items():
                        f.write(
                            f"  {method}: {timing['duration_seconds']:.3f}s ({timing['results_count']} results)\n"
                        )

                f.write("\n")

            # Search effectiveness summary
            f.write("SEARCH EFFECTIVENESS SUMMARY\n")
            f.write("-" * 30 + "\n")

            for query, query_results in results["results"].items():
                f.write(f"\nQuery: {query}\n")

                if "search_comparison" in query_results:
                    search_comp = query_results["search_comparison"]["search_types"]

                    # Compare result counts
                    if "keyword_only" in search_comp:
                        f.write(
                            f"  Keyword-only results: {len(search_comp['keyword_only'])}\n"
                        )
                    if "semantic_only" in search_comp:
                        f.write(
                            f"  Semantic-only results: {len(search_comp['semantic_only'])}\n"
                        )

                    # Best alpha value
                    if "hybrid_alpha_comparison" in search_comp:
                        best_alpha = None
                        max_results = 0
                        for alpha_key, alpha_results in search_comp[
                            "hybrid_alpha_comparison"
                        ].items():
                            if len(alpha_results) > max_results:
                                max_results = len(alpha_results)
                                best_alpha = alpha_key
                        f.write(
                            f"  Best alpha value: {best_alpha} ({max_results} results)\n"
                        )

                f.write("\n")

        logger.info(f"Summary report saved to: {output_file}")


def main():
    """Main function to run search tests."""
    logger.info("Starting Typesense Hybrid & Multi-Search Testing")

    try:
        tester = SearchTester()
        results = tester.run_comprehensive_test_suite()

        logger.info("All tests completed successfully!")

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise


if __name__ == "__main__":
    main()
