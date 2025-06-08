#!/usr/bin/env python3
"""
Test semantic search functionality using TypeSense multi_search endpoint for large embeddings.
"""

import os
import sys
import json
import traceback
from typing import List, Dict, Any

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.config import get_config
from data.optimized_rag_pipeline import EmbeddingProvider
import typesense


def test_semantic_search_multi():
    """Test semantic search using multi_search endpoint for large embeddings."""
    print("Testing semantic search with multi_search endpoint...\n")

    # Load config
    config = get_config()

    # Create TypeSense client
    client = typesense.Client(
        {
            "api_key": "xyz",
            "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
            "connection_timeout_seconds": 10,
        }
    )

    # Create embedding provider
    embedding_provider = EmbeddingProvider(config)

    # Test queries
    test_queries = [
        "How to use pandas for data analysis?",
        "What are large language models?",
        "How to deploy FastAPI applications?",
    ]

    # Get available collections
    try:
        collections_response = client.collections.retrieve()
        available_collections = [
            col["name"] for col in collections_response if col["name"]
        ]
        print(f"Available collections ({len(available_collections)}):")
        for i, collection in enumerate(available_collections, 1):
            print(f"  {i}. {collection}")
        print()
    except Exception as e:
        print(f"❌ Error retrieving collections: {e}")
        return

    # Focus on key collections for testing
    target_collections = [
        "unified_knowledge_base",
        "chapters_data_analysis",
        "chapters_large_language_models",
        "chapters_deployment_tools",
        "discourse_posts_optimized",
    ]

    # Filter to only collections that exist
    test_collections = [
        col for col in target_collections if col in available_collections
    ]

    print(f"Testing semantic search on {len(test_collections)} collections:")
    for col in test_collections:
        print(f"  • {col}")
    print()

    # Test each query
    for query_idx, query in enumerate(test_queries, 1):
        print(f"🔍 Query {query_idx}: '{query}'")
        print("-" * 60)

        try:
            # Generate embedding for the query
            print("  Generating query embedding...")
            embeddings = embedding_provider.generate_embeddings([query])

            if not embeddings or not embeddings[0]:
                print("  ❌ Failed to generate embedding for query")
                continue

            query_embedding = embeddings[0]
            print(f"  ✅ Query embedding generated ({len(query_embedding)} dimensions)")

            # Prepare multi-search requests
            search_requests = []

            for collection_name in test_collections:
                search_request = {
                    "searches": [
                        {
                            "collection": collection_name,
                            "q": "*",
                            "vector_query": {"embedding": query_embedding, "k": 3},
                            "per_page": 3,
                            "include_fields": "content,module,file_path",
                        }
                    ]
                }
                search_requests.append((collection_name, search_request))

            total_results = 0

            # Execute searches one by one
            for collection_name, search_request in search_requests:
                try:
                    response = client.multi_search.perform(search_request, {})

                    if "results" in response and len(response["results"]) > 0:
                        search_result = response["results"][0]
                        hits = search_result.get("hits", [])

                        if hits:
                            total_results += len(hits)
                            print(f"  📚 {collection_name}: {len(hits)} results")

                            # Show top result
                            top_result = hits[0]
                            doc = top_result["document"]
                            vector_distance = top_result.get("vector_distance", "N/A")
                            content = doc.get("content", "No content")

                            # Truncate content for display
                            content_preview = (
                                content[:100] + "..." if len(content) > 100 else content
                            )
                            print(f"    Top result (distance: {vector_distance}):")
                            print(f"    {content_preview}")
                        else:
                            print(f"  📚 {collection_name}: No results")
                    else:
                        print(f"  📚 {collection_name}: No search results")

                except Exception as e:
                    if "does not have a field named" in str(e):
                        print(f"  ⚠️  {collection_name}: Missing vector field")
                    else:
                        print(f"  ❌ {collection_name}: Error - {e}")

            print(f"  📊 Total results found: {total_results}")
            print()

        except Exception as e:
            print(f"  ❌ Error processing query: {e}")
            print()

    # Test text search for comparison
    print("🔍 Testing text-only search for comparison...")
    print("-" * 60)

    test_query = "pandas dataframe"

    for collection_name in test_collections[:2]:  # Test on first 2 collections
        try:
            search_params = {"q": test_query, "query_by": "content", "per_page": 2}

            search_result = client.collections[collection_name].documents.search(
                search_params
            )
            hits = search_result.get("hits", [])

            print(f"  📚 {collection_name}: {len(hits)} text results")

            if hits:
                top_result = hits[0]
                doc = top_result["document"]
                text_score = top_result.get("text_match", "N/A")
                content = doc.get("content", "No content")

                content_preview = content[:80] + "..." if len(content) > 80 else content
                print(f"    Top text result (score: {text_score}):")
                print(f"    {content_preview}")

        except Exception as e:
            print(f"  ❌ {collection_name}: Text search error - {e}")

    print("\n✅ Semantic search testing completed!")


if __name__ == "__main__":
    test_semantic_search_multi()
