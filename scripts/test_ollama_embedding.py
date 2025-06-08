#!/usr/bin/env python3
"""
Test Ollama embedding generation to verify it's working correctly.
"""

import os
import sys
import requests
import json

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.config import get_config


def test_ollama_embedding():
    """Test Ollama embedding generation."""
    print(
        "Testing Ollama embedding generation...\n"
    )  # Load config to get the embedding settings
    config = get_config()
    embedding_config = config.embeddings

    print(f"Config embedding provider: {config.defaults.embedding_provider}")
    print(f"Config ollama embedding model: {embedding_config.ollama.model}")
    print(f"Config ollama embedding dimensions: {embedding_config.ollama.dimensions}")
    print()

    # Test text
    test_text = (
        "This is a test sentence to check if Ollama embeddings are working correctly."
    )

    # Make direct API call to Ollama
    try:
        print("Making direct API call to Ollama...")

        payload = {"model": "nomic-embed-text", "input": test_text}

        response = requests.post(
            "http://localhost:11434/api/embed", json=payload, timeout=30
        )

        if response.status_code == 200:
            result = response.json()

            if "embeddings" in result and len(result["embeddings"]) > 0:
                embedding = result["embeddings"][0]
                dimensions = len(embedding)

                print(f"✅ Ollama API call successful!")
                print(f"   Embedding dimensions: {dimensions}")
                print(f"   First 5 values: {embedding[:5]}")
                print(f"   Model used: nomic-embed-text")

                if dimensions == 768:
                    print(f"   ✅ Correct dimensions (768 for nomic-embed-text)")
                else:
                    print(
                        f"   ⚠️  Unexpected dimensions (expected 768, got {dimensions})"
                    )

            else:
                print(f"❌ No embeddings in response: {result}")
        else:
            print(f"❌ Ollama API call failed: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ Error calling Ollama API: {e}")

    print()

    # Test using the RAG pipeline's embedding function
    try:
        print("Testing through RAG pipeline embedding function...")

        # Import the optimized RAG pipeline
        from data.optimized_rag_pipeline import EmbeddingProvider

        # Create embedding provider
        embedding_provider = EmbeddingProvider(config)

        # Generate embedding - fix method call to use generate_embeddings (plural)
        embeddings = embedding_provider.generate_embeddings([test_text])

        if embeddings and embeddings[0]:
            embedding = embeddings[0]
            dimensions = len(embedding)
            print(f"✅ RAG pipeline embedding successful!")
            print(f"   Embedding dimensions: {dimensions}")
            print(f"   First 5 values: {embedding[:5]}")

            if dimensions == 768:
                print(f"   ✅ Correct dimensions (768 for nomic-embed-text)")
            else:
                print(f"   ⚠️  Unexpected dimensions (expected 768, got {dimensions})")
        else:
            print(f"❌ RAG pipeline returned no embedding")

    except Exception as e:
        print(f"❌ Error testing RAG pipeline embedding: {e}")


if __name__ == "__main__":
    test_ollama_embedding()
