#!/usr/bin/env python3
"""
Test semantic search functionality across TypeSense collections using Ollama embeddings.
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


def test_semantic_search():
    """Test semantic search across collections."""
    print("Testing semantic search functionality...\n")

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
        "What is machine learning?",
        "How to deploy a FastAPI application?",
        "What are large language models?",
        "How to visualize data using matplotlib?",
    ]

    print(f"Testing {len(test_queries)} queries across available collections...\n")

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

    # Test each query
    for query_idx, query in enumerate(test_queries, 1):
        print(f"🔍 Query {query_idx}: '{query}'")
        print("-" * 50)

        try:
            # Generate embedding for the query
            print("  Generating query embedding...")
            embeddings = embedding_provider.generate_embeddings([query])

            if not embeddings or not embeddings[0]:
                print("  ❌ Failed to generate embedding for query")
                continue

            query_embedding = embeddings[0]
            print(f"  ✅ Query embedding generated ({len(query_embedding)} dimensions)")

            # Test semantic search on each collection
            results_found = 0

            for collection_name in available_collections:
                try:
                    # Perform vector search
                    search_params = {
                        "q": "*",
                        "vector_query": f'embedding:([{",".join(map(str, query_embedding))}], k:3)',
                        "per_page": 3,
                    }

                    search_result = client.collections[
                        collection_name
                    ].documents.search(search_params)

                    hits = search_result.get("hits", [])
                    if hits:
                        results_found += len(hits)
                        print(f"  📚 {collection_name}: {len(hits)} results")

                        # Show top result details
                        top_result = hits[0]
                        doc = top_result["document"]
                        score = top_result.get("vector_distance", "N/A")
                        content = doc.get("content", "No content")

                        # Truncate content for display
                        content_preview = (
                            content[:100] + "..." if len(content) > 100 else content
                        )
                        print(f"    Top result (score: {score}):")
                        print(f"    {content_preview}")

                except Exception as e:
                    if "does not have a field named `embedding`" in str(e):
                        print(f"  ⚠️  {collection_name}: No embedding field")
                    elif "Collection `" in str(e) and "` not found" in str(e):
                        print(f"  ⚠️  {collection_name}: Collection not found")
                    else:
                        print(f"  ❌ {collection_name}: Error - {e}")

            print(f"  📊 Total results found: {results_found}")
            print()

        except Exception as e:
            print(f"  ❌ Error processing query: {e}")
            print(f"  Traceback: {traceback.format_exc()}")
            print()

    # Test hybrid search (text + vector)
    print("🔍 Testing hybrid search (text + vector)...")
    print("-" * 50)

    test_query = "pandas dataframe analysis"

    try:
        # Generate embedding
        embeddings = embedding_provider.generate_embeddings([test_query])
        if embeddings and embeddings[0]:
            query_embedding = embeddings[0]

            # Test on unified_knowledge_base collection if available
            target_collection = "unified_knowledge_base"
            if target_collection in available_collections:
                print(f"Testing hybrid search on '{target_collection}' collection...")

                # Hybrid search parameters
                search_params = {
                    "q": test_query,
                    "query_by": "content",
                    "vector_query": f'embedding:([{",".join(map(str, query_embedding))}], k:5)',
                    "per_page": 5,
                    "num_typos": 1,
                }

                search_result = client.collections[target_collection].documents.search(
                    search_params
                )
                hits = search_result.get("hits", [])

                print(f"✅ Hybrid search results: {len(hits)} documents")

                for i, hit in enumerate(hits[:3], 1):
                    doc = hit["document"]
                    text_score = hit.get("text_match", "N/A")
                    vector_score = hit.get("vector_distance", "N/A")
                    content = doc.get("content", "No content")

                    content_preview = (
                        content[:120] + "..." if len(content) > 120 else content
                    )
                    print(f"  {i}. Text: {text_score}, Vector: {vector_score}")
                    print(f"     {content_preview}")
                    print()
            else:
                print(f"⚠️  Target collection '{target_collection}' not available")

    except Exception as e:
        print(f"❌ Error in hybrid search test: {e}")

    print("✅ Semantic search testing completed!")


if __name__ == "__main__":
    test_semantic_search()
