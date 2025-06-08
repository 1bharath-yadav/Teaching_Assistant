#!/usr/bin/env python3
"""
Test semantic search functionality with Ollama embeddings across TypeSense collections.
This tests the actual search pipeline that the API uses.
"""

import json
import logging
import sys
import os
from pathlib import Path

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from lib.config import get_config
from lib.embeddings import generate_embedding
from api.core.clients import typesense_client
from api.models.schemas import QuestionRequest
from api.services.search_service import hybrid_search_across_collections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


def test_embedding_generation():
    """Test that we can generate embeddings using Ollama"""
    test_question = "What are the benefits of using TypeSense for search?"

    logger.info(f"Testing embedding generation for: '{test_question}'")

    try:
        embedding = generate_embedding(test_question)
        logger.info(
            f"✅ Successfully generated embedding with {len(embedding)} dimensions"
        )
        logger.info(f"   First 5 values: {embedding[:5]}")

        # Verify it's using Ollama (768 dimensions)
        if len(embedding) == 768:
            logger.info("✅ Using Ollama embeddings (768 dimensions)")
        elif len(embedding) == 1536:
            logger.warning("⚠️  Using OpenAI embeddings (1536 dimensions)")
        else:
            logger.warning(f"⚠️  Unexpected embedding dimension: {len(embedding)}")

        return embedding
    except Exception as e:
        logger.error(f"❌ Failed to generate embedding: {e}")
        return None


def test_collections_available():
    """Test which collections are available in TypeSense"""
    logger.info("Testing available TypeSense collections...")

    try:
        collections_response = typesense_client.collections.retrieve()
        collections = [col["name"] for col in collections_response]

        logger.info(f"✅ Found {len(collections)} collections:")
        for col in collections:
            logger.info(f"   - {col}")

        return collections
    except Exception as e:
        logger.error(f"❌ Failed to retrieve collections: {e}")
        return []


async def test_hybrid_search():
    """Test the hybrid search functionality"""
    test_questions = [
        "What is machine learning?",
        "How do I use TypeSense for vector search?",
        "What are the benefits of RAG systems?",
        "How do I deploy applications with Docker?",
        "What is the difference between supervised and unsupervised learning?",
    ]

    # Get available collections
    collections = test_collections_available()
    if not collections:
        logger.error("❌ No collections available for testing")
        return

    # Test a few collections (not all to keep output manageable)
    test_collections = collections[:3]

    for question in test_questions:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing question: '{question}'")
        logger.info(f"{'='*60}")

        try:
            # Create request payload
            payload = QuestionRequest(question=question)

            # Perform hybrid search
            results = await hybrid_search_across_collections(
                payload=payload,
                collections=test_collections,
                alpha=0.7,  # 70% vector, 30% text
                top_k=3,
            )

            logger.info(f"✅ Found {len(results)} results")

            # Display top results
            for i, result in enumerate(results[:3], 1):
                doc = result["document"]
                collection = result["collection"]
                text_match = result.get("text_match", 0)
                vector_distance = result.get("vector_distance", "N/A")

                content_preview = (
                    doc.get("content", "")[:200] + "..."
                    if len(doc.get("content", "")) > 200
                    else doc.get("content", "")
                )

                logger.info(f"\n   Result {i} (from {collection}):")
                logger.info(f"   Text Match Score: {text_match}")
                logger.info(f"   Vector Distance: {vector_distance}")
                logger.info(f"   Content: {content_preview}")

        except Exception as e:
            logger.error(f"❌ Search failed for question '{question}': {e}")
            import traceback

            traceback.print_exc()


async def main():
    """Main test function"""
    logger.info("🚀 Starting semantic search tests with Ollama embeddings")

    # Test 1: Embedding generation
    embedding = test_embedding_generation()
    if not embedding:
        logger.error("❌ Cannot proceed without working embeddings")
        return

    # Test 2: Collections availability
    collections = test_collections_available()
    if not collections:
        logger.error("❌ Cannot proceed without available collections")
        return

    # Test 3: Hybrid search functionality
    await test_hybrid_search()

    logger.info("\n🎉 Semantic search testing completed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
