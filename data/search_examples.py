#!/usr/bin/env python3
"""
Typesense Hybrid Search & Multi-Search Examples

This script demonstrates specific examples from the official Typesense documentation:
- https://typesense.org/docs/28.0/api/vector-search.html#hybrid-search
- https://typesense.org/docs/28.0/api/federated-multi-search.html#federated-search

Examples include:
1. Basic hybrid search with alpha weighting
2. Semantic search using auto-embedding
3. Federated search across multiple collections
4. Union search with merged results
5. Similar document search using document ID
6. Advanced filtering and distance thresholds
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from optimized_rag_pipeline import OptimizedRAGPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_hybrid_search_alpha_weighting():
    """Demonstrate hybrid search with different alpha weightings."""
    logger.info("=== Demo: Hybrid Search with Alpha Weighting ===")

    pipeline = OptimizedRAGPipeline()
    query = "machine learning algorithms"

    # Test different alpha values as per documentation
    alpha_values = [0.1, 0.3, 0.5, 0.7, 0.9]

    for alpha in alpha_values:
        logger.info(
            f"\nTesting alpha={alpha} (vector weight={alpha}, keyword weight={1-alpha})"
        )

        results = pipeline.test_hybrid_search(query, alpha=alpha)

        logger.info(f"  Results found: {len(results)}")
        if results:
            top_result = results[0]
            logger.info(f"  Top result: {top_result['content'][:100]}...")
            logger.info(
                f"  Text match score: {top_result.get('text_match_score', 'N/A')}"
            )
            logger.info(
                f"  Vector distance: {top_result.get('vector_distance', 'N/A')}"
            )

    return {"demo": "hybrid_search_alpha", "query": query, "alpha_values": alpha_values}


def demo_semantic_vs_keyword_search():
    """Compare pure semantic vs pure keyword search."""
    logger.info("=== Demo: Semantic vs Keyword Search Comparison ===")

    pipeline = OptimizedRAGPipeline()
    query = "data visualization techniques"

    logger.info(f"Query: '{query}'")

    # Pure semantic search (alpha=1.0)
    logger.info("\n1. Pure Semantic Search (alpha=1.0):")
    semantic_results = pipeline.test_semantic_search(query)
    logger.info(f"   Found {len(semantic_results)} results")
    if semantic_results:
        logger.info(f"   Top result: {semantic_results[0]['content'][:100]}...")

    # Pure keyword search (alpha=0.0) - achieved by not using vector_query
    logger.info("\n2. Pure Keyword Search:")
    try:
        keyword_response = pipeline.client.multi_search.perform(
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
        keyword_results = pipeline._parse_search_response(keyword_response, "keyword")
        logger.info(f"   Found {len(keyword_results)} results")
        if keyword_results:
            logger.info(f"   Top result: {keyword_results[0]['content'][:100]}...")
    except Exception as e:
        logger.error(f"   Keyword search failed: {e}")
        keyword_results = []

    # Balanced hybrid search (alpha=0.5)
    logger.info("\n3. Balanced Hybrid Search (alpha=0.5):")
    hybrid_results = pipeline.test_hybrid_search(query, alpha=0.5)
    logger.info(f"   Found {len(hybrid_results)} results")
    if hybrid_results:
        logger.info(f"   Top result: {hybrid_results[0]['content'][:100]}...")

    return {
        "demo": "semantic_vs_keyword",
        "query": query,
        "semantic_count": len(semantic_results),
        "keyword_count": len(keyword_results),
        "hybrid_count": len(hybrid_results),
    }


def demo_federated_search():
    """Demonstrate federated search across multiple collections."""
    logger.info("=== Demo: Federated Search Across Collections ===")

    pipeline = OptimizedRAGPipeline()
    query = "python programming"

    # Get available collections
    try:
        collections_response = pipeline.client.collections.retrieve()
        available_collections = [col["name"] for col in collections_response]
        logger.info(f"Available collections: {available_collections}")

        # Use first 3 collections for demo
        test_collections = available_collections[:3]

    except Exception as e:
        logger.error(f"Failed to get collections: {e}")
        test_collections = ["unified_knowledge_base"]

    logger.info(f"\nSearching across collections: {test_collections}")
    logger.info(f"Query: '{query}'")

    # Federated search
    federated_results = pipeline.test_federated_search(query, test_collections)

    total_results = 0
    for collection_name, results in federated_results.items():
        logger.info(f"\nCollection '{collection_name}': {len(results)} results")
        total_results += len(results)

        if results:
            top_result = results[0]
            logger.info(f"  Top result: {top_result['content'][:80]}...")

    logger.info(f"\nTotal results across all collections: {total_results}")

    return {
        "demo": "federated_search",
        "query": query,
        "collections": test_collections,
        "total_results": total_results,
    }


def demo_union_search():
    """Demonstrate union search with merged results."""
    logger.info("=== Demo: Union Search with Merged Results ===")

    pipeline = OptimizedRAGPipeline()
    query = "data analysis"

    logger.info(f"Query: '{query}'")
    logger.info(
        "Union search merges results from multiple searches into single ranked list"
    )

    # Union search
    union_results = pipeline.test_union_search(query)

    logger.info(f"\nUnion search found {len(union_results)} merged results")

    for i, result in enumerate(union_results[:5], 1):  # Show top 5
        logger.info(f"{i}. [{result['source']}] {result['content'][:80]}...")
        logger.info(
            f"   Text score: {result.get('text_match_score', 'N/A')}, "
            f"Vector distance: {result.get('vector_distance', 'N/A')}"
        )

    return {
        "demo": "union_search",
        "query": query,
        "merged_results": len(union_results),
    }


def demo_distance_threshold_filtering():
    """Demonstrate distance threshold for filtering results."""
    logger.info("=== Demo: Distance Threshold Filtering ===")

    pipeline = OptimizedRAGPipeline()
    query = "statistical methods"

    logger.info(f"Query: '{query}'")
    logger.info("Testing different distance thresholds to filter results by relevance")

    thresholds = [0.3, 0.5, 0.7, 0.9]

    for threshold in thresholds:
        logger.info(f"\nTesting distance threshold: {threshold}")

        results = pipeline.test_advanced_hybrid_search(
            query, distance_threshold=threshold, alpha=0.7
        )

        logger.info(f"  Results found: {len(results)}")
        if results:
            avg_distance = sum(
                r.get("vector_distance", 0) for r in results if r.get("vector_distance")
            ) / len(results)
            logger.info(f"  Average vector distance: {avg_distance:.3f}")

    return {
        "demo": "distance_threshold",
        "query": query,
        "thresholds_tested": thresholds,
    }


def demo_similar_document_search():
    """Demonstrate finding similar documents using document ID."""
    logger.info("=== Demo: Similar Document Search ===")

    pipeline = OptimizedRAGPipeline()

    # First, get a document ID from a search
    logger.info("Step 1: Finding a document to use as reference...")

    initial_results = pipeline.test_hybrid_search("machine learning", alpha=0.7)

    if not initial_results:
        logger.error("No documents found for similarity search demo")
        return {"demo": "similar_document", "error": "No reference document found"}

    reference_doc = initial_results[0]
    doc_id = reference_doc["id"]

    logger.info(f"Step 2: Using document ID '{doc_id}' to find similar documents")
    logger.info(f"Reference document: {reference_doc['content'][:100]}...")

    # Find similar documents
    similar_results = pipeline.test_similar_document_search(doc_id)

    logger.info(f"\nFound {len(similar_results)} similar documents:")

    for i, result in enumerate(similar_results[:3], 1):
        logger.info(f"{i}. {result['content'][:80]}...")
        logger.info(f"   Vector distance: {result.get('vector_distance', 'N/A')}")

    return {
        "demo": "similar_document",
        "reference_doc_id": doc_id,
        "similar_docs_found": len(similar_results),
    }


def demo_advanced_filtering():
    """Demonstrate advanced filtering capabilities."""
    logger.info("=== Demo: Advanced Filtering ===")

    pipeline = OptimizedRAGPipeline()
    query = "programming"

    filters = [
        ("has_code:true", "Documents with code"),
        ("content_length:>500", "Long documents (>500 chars)"),
        ("source_type:discourse", "Discourse posts only"),
        ("source_type:chapters", "Chapter content only"),
    ]

    logger.info(f"Query: '{query}'")
    logger.info("Testing different filters:")

    for filter_expr, description in filters:
        logger.info(f"\nFilter: {description} ({filter_expr})")

        try:
            results = pipeline.test_advanced_hybrid_search(
                query, filters=filter_expr, alpha=0.7
            )

            logger.info(f"  Results found: {len(results)}")
            if results:
                logger.info(f"  Top result: {results[0]['content'][:80]}...")

        except Exception as e:
            logger.error(f"  Filter failed: {e}")

    return {
        "demo": "advanced_filtering",
        "query": query,
        "filters_tested": [f[0] for f in filters],
    }


def main():
    """Run all demonstration examples."""
    logger.info("TYPESENSE HYBRID & MULTI-SEARCH DEMONSTRATIONS")
    logger.info("=" * 60)

    demos = [
        demo_hybrid_search_alpha_weighting,
        demo_semantic_vs_keyword_search,
        demo_federated_search,
        demo_union_search,
        demo_distance_threshold_filtering,
        demo_similar_document_search,
        demo_advanced_filtering,
    ]

    results = []

    for demo_func in demos:
        try:
            logger.info(f"\n{'-' * 60}")
            result = demo_func()
            results.append(result)
            logger.info("Demo completed successfully!")

        except Exception as e:
            logger.error(f"Demo failed: {e}")
            results.append({"demo": demo_func.__name__, "error": str(e)})

    # Save all demo results
    output_file = current_dir / "search_demo_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'-' * 60}")
    logger.info("All demonstrations completed!")
    logger.info(f"Results saved to: {output_file}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
