#!/usr/bin/env python3
"""
Test the Teaching Assistant API endpoints to verify end-to-end functionality
with Ollama embeddings.
"""

import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"


def test_api_endpoints():
    """Test the main API endpoints"""

    test_questions = [
        "What is machine learning and how is it used in data science?",
        "How do I use TypeSense for vector search?",
        "What are the benefits of RAG systems?",
        "How do I deploy applications with Docker?",
        "Explain the difference between supervised and unsupervised learning.",
    ]

    # Test the main ask endpoint
    logger.info("🚀 Testing /api/v1/ask endpoint...")

    for i, question in enumerate(test_questions, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test {i}: {question}")
        logger.info(f"{'='*60}")

        try:
            payload = {"question": question}

            start_time = time.time()
            response = requests.post(
                f"{API_BASE}/api/v1/ask",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            end_time = time.time()

            if response.status_code == 200:
                result = response.json()

                logger.info(f"✅ Success! Response time: {end_time - start_time:.2f}s")
                logger.info(f"   Answer: {result.get('answer', 'No answer')[:200]}...")
                logger.info(
                    f"   Collections used: {result.get('collections_used', [])}"
                )
                logger.info(
                    f"   Search results count: {len(result.get('search_results', []))}"
                )

                # Show first search result
                search_results = result.get("search_results", [])
                if search_results:
                    first_result = search_results[0]
                    content = first_result.get("document", {}).get("content", "")[:150]
                    collection = first_result.get("collection", "unknown")
                    logger.info(f"   First result from {collection}: {content}...")

            else:
                logger.error(f"❌ Request failed with status {response.status_code}")
                logger.error(f"   Response: {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")


def test_search_only_endpoint():
    """Test the search-only endpoint"""
    logger.info("\n🔍 Testing /api/v1/search endpoint...")

    test_question = "What is machine learning?"

    try:
        payload = {"question": test_question}

        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/api/v1/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        end_time = time.time()

        if response.status_code == 200:
            result = response.json()

            logger.info(
                f"✅ Search Success! Response time: {end_time - start_time:.2f}s"
            )
            logger.info(f"   Results count: {len(result.get('results', []))}")
            logger.info(
                f"   Collections searched: {result.get('collections_used', [])}"
            )

            # Show search results
            results = result.get("results", [])
            for i, search_result in enumerate(results[:3], 1):
                content = search_result.get("document", {}).get("content", "")[:100]
                collection = search_result.get("collection", "unknown")
                text_match = search_result.get("text_match", 0)
                vector_distance = search_result.get("vector_distance", "N/A")

                logger.info(f"   Result {i} ({collection}): {content}...")
                logger.info(
                    f"      Text match: {text_match}, Vector distance: {vector_distance}"
                )

        else:
            logger.error(f"❌ Search failed with status {response.status_code}")
            logger.error(f"   Response: {response.text}")

    except Exception as e:
        logger.error(f"❌ Search request failed: {e}")


def check_api_status():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API is running and accessible")
            return True
        else:
            logger.error(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to API: {e}")
        return False


def main():
    """Main test function"""
    logger.info("🚀 Starting API endpoint tests with Ollama embeddings")

    # Check if API is running
    if not check_api_status():
        logger.error(
            "❌ API is not accessible. Make sure it's running on http://localhost:8000"
        )
        logger.info(
            "💡 You can start it with: cd /home/archer/projects/llm_tests/Teaching_Assistant && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"
        )
        return

    # Test main ask endpoint
    test_api_endpoints()

    # Test search-only endpoint
    test_search_only_endpoint()

    logger.info("\n🎉 API endpoint testing completed!")


if __name__ == "__main__":
    main()
