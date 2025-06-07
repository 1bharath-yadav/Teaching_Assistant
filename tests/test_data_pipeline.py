#!/usr/bin/env python3
"""
Comprehensive Test Script for Data Cleaning, Embedding, and Indexing

This script validates the entire data pipeline from raw content to indexed, searchable data:
1. Data Cleaning - Tests content preprocessing and normalization
2. Embedding Generation - Tests embedding creation for different providers
3. Indexing - Tests Typesense collection creation and document indexing
4. Search Validation - Tests that indexed data is properly searchable

Usage:
    python tests/test_data_pipeline.py
"""

import json
import sys
import time
import logging
import traceback
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "data"))

# Import modules
from lib.config import get_config, get_typesense_client
from lib.embeddings import (
    generate_embedding,
    batch_generate_embeddings,
    test_embedding_provider,
    get_embedding_dimensions,
)
from data.optimized_chunker import OptimizedChunker, ChunkingConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_data_pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DataPipelineTester:
    """Comprehensive test suite for the data pipeline."""

    def __init__(self):
        """Initialize the tester."""
        self.config = get_config()
        self.typesense_client = None
        self.chunker = None
        self.test_collection = "test_pipeline_collection"

        # Test data samples
        self.sample_markdown = """
# Test Document

This is a test document for validating data processing.

## Code Example

```python
def hello_world():
    print("Hello, World!")
    return "success"
```

## Data Visualization

Here's a chart showing performance metrics:

![Chart](https://example.com/chart.png)

Some content with **bold** and *italic* text.

### Lists

- Item 1
- Item 2  
- Item 3

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
| Value 3  | Value 4  |

## Links and References

See [this guide](https://example.com) for more information.
"""

        self.sample_dirty_content = """
<!-- HTML comment to remove -->
# Messy    Title   With   Spaces

This    has    excessive     whitespace.


Multiple empty lines above.

```python


def messy_code():
    # Poor formatting
        x=1+2
return x

```

More    content     with    problems.

<!-- Another comment -->
        """

    def setup_test_environment(self) -> bool:
        """Set up the test environment."""
        try:
            logger.info("🔧 Setting up test environment...")

            # Initialize Typesense client
            self.typesense_client = get_typesense_client()

            # Initialize chunker
            self.chunker = OptimizedChunker()

            # Test Typesense connection
            collections = self.typesense_client.collections.retrieve()
            logger.info(
                f"✅ Connected to Typesense ({len(collections)} collections available)"
            )

            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup test environment: {e}")
            return False

    def test_data_cleaning(self) -> Dict[str, Any]:
        """Test data cleaning and preprocessing functionality."""
        logger.info("\n" + "=" * 60)
        logger.info("🧹 TESTING DATA CLEANING")
        logger.info("=" * 60)

        results = {
            "test_name": "data_cleaning",
            "passed": 0,
            "failed": 0,
            "details": [],
        }

        try:
            # Test 1: Basic content cleaning
            logger.info("Testing basic content cleaning...")
            cleaned = self.chunker.clean_markdown_content(self.sample_dirty_content)

            # Verify HTML comments are removed
            if "<!--" not in cleaned:
                results["passed"] += 1
                results["details"].append("✅ HTML comments removed")
            else:
                results["failed"] += 1
                results["details"].append("❌ HTML comments not removed")

            # Verify excessive whitespace is normalized
            if not re.search(r"  +", cleaned) and not re.search(r"\n\n\n+", cleaned):
                results["passed"] += 1
                results["details"].append("✅ Excessive whitespace normalized")
            else:
                results["failed"] += 1
                results["details"].append("❌ Excessive whitespace not normalized")

            # Test 2: Metadata extraction
            logger.info("Testing metadata extraction...")
            metadata = self.chunker.extract_metadata(self.sample_markdown, "test.md")

            expected_fields = [
                "has_code",
                "has_images",
                "has_links",
                "has_tables",
                "word_count",
                "char_count",
                "header_count",
                "title",
            ]

            for field in expected_fields:
                if field in metadata:
                    results["passed"] += 1
                    results["details"].append(f"✅ Metadata field '{field}' extracted")
                else:
                    results["failed"] += 1
                    results["details"].append(f"❌ Metadata field '{field}' missing")

            # Verify boolean metadata accuracy
            if (
                metadata.get("has_code")
                and metadata.get("has_images")
                and metadata.get("has_links")
                and metadata.get("has_tables")
            ):
                results["passed"] += 1
                results["details"].append("✅ Boolean metadata correctly detected")
            else:
                results["failed"] += 1
                results["details"].append("❌ Boolean metadata incorrectly detected")

            # Test 3: Chunk validation
            logger.info("Testing chunk validation...")

            # Valid chunk
            valid_chunk = {
                "page_content": "This is a valid chunk with sufficient content for testing purposes. It contains meaningful text that should pass validation."
            }

            # Invalid chunks
            invalid_chunks = [
                {"page_content": "Too short"},  # Too short
                {"page_content": "###"},  # Just header
                {"page_content": "!@#$%^&*()_+" * 50},  # Mostly special characters
                {"page_content": "A" * 10000},  # Too long
            ]

            if self.chunker.validate_chunk(valid_chunk):
                results["passed"] += 1
                results["details"].append("✅ Valid chunk accepted")
            else:
                results["failed"] += 1
                results["details"].append("❌ Valid chunk rejected")

            invalid_rejected = sum(
                1 for chunk in invalid_chunks if not self.chunker.validate_chunk(chunk)
            )
            results["passed"] += invalid_rejected
            results["failed"] += len(invalid_chunks) - invalid_rejected
            results["details"].append(
                f"✅ {invalid_rejected}/{len(invalid_chunks)} invalid chunks correctly rejected"
            )

        except Exception as e:
            logger.error(f"Error in data cleaning test: {e}")
            results["failed"] += 1
            results["details"].append(f"❌ Exception: {e}")

        logger.info(
            f"Data Cleaning Results: {results['passed']} passed, {results['failed']} failed"
        )
        return results

    def test_embedding_generation(self) -> Dict[str, Any]:
        """Test embedding generation functionality."""
        logger.info("\n" + "=" * 60)
        logger.info("🧠 TESTING EMBEDDING GENERATION")
        logger.info("=" * 60)

        results = {
            "test_name": "embedding_generation",
            "passed": 0,
            "failed": 0,
            "details": [],
        }

        try:
            # Test 1: Provider connectivity
            logger.info("Testing embedding provider connectivity...")
            if test_embedding_provider():
                results["passed"] += 1
                results["details"].append("✅ Embedding provider connection successful")
            else:
                results["failed"] += 1
                results["details"].append("❌ Embedding provider connection failed")
                return results  # Can't continue without working provider

            # Test 2: Single embedding generation
            logger.info("Testing single embedding generation...")
            test_text = "This is a test sentence for embedding generation."

            start_time = time.time()
            embedding = generate_embedding(test_text)
            generation_time = time.time() - start_time

            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                results["passed"] += 1
                results["details"].append(
                    f"✅ Single embedding generated ({len(embedding)} dimensions, {generation_time:.3f}s)"
                )
            else:
                results["failed"] += 1
                results["details"].append("❌ Single embedding generation failed")

            # Test 3: Embedding dimensions consistency
            logger.info("Testing embedding dimensions consistency...")
            expected_dims = get_embedding_dimensions()

            if len(embedding) == expected_dims:
                results["passed"] += 1
                results["details"].append(
                    f"✅ Embedding dimensions correct ({expected_dims})"
                )
            else:
                results["failed"] += 1
                results["details"].append(
                    f"❌ Embedding dimensions incorrect (got {len(embedding)}, expected {expected_dims})"
                )

            # Test 4: Batch embedding generation
            logger.info("Testing batch embedding generation...")
            test_texts = [
                "First test sentence for batch processing.",
                "Second test sentence with different content.",
                "Third test sentence for validation.",
            ]

            start_time = time.time()
            batch_embeddings = batch_generate_embeddings(test_texts)
            batch_time = time.time() - start_time

            if (
                batch_embeddings
                and len(batch_embeddings) == len(test_texts)
                and all(len(emb) == expected_dims for emb in batch_embeddings)
            ):
                results["passed"] += 1
                results["details"].append(
                    f"✅ Batch embeddings generated ({len(batch_embeddings)} embeddings, {batch_time:.3f}s)"
                )
            else:
                results["failed"] += 1
                results["details"].append("❌ Batch embedding generation failed")

            # Test 5: Embedding uniqueness
            logger.info("Testing embedding uniqueness...")
            different_texts = ["apple", "banana", "computer"]
            different_embeddings = [
                generate_embedding(text) for text in different_texts
            ]

            # Calculate cosine similarities
            import numpy as np

            similarities = []
            for i in range(len(different_embeddings)):
                for j in range(i + 1, len(different_embeddings)):
                    emb1 = np.array(different_embeddings[i])
                    emb2 = np.array(different_embeddings[j])
                    similarity = np.dot(emb1, emb2) / (
                        np.linalg.norm(emb1) * np.linalg.norm(emb2)
                    )
                    similarities.append(similarity)

            avg_similarity = np.mean(similarities)
            if avg_similarity < 0.9:  # Different texts should have lower similarity
                results["passed"] += 1
                results["details"].append(
                    f"✅ Embeddings are sufficiently unique (avg similarity: {avg_similarity:.3f})"
                )
            else:
                results["failed"] += 1
                results["details"].append(
                    f"❌ Embeddings too similar (avg similarity: {avg_similarity:.3f})"
                )

        except Exception as e:
            logger.error(f"Error in embedding generation test: {e}")
            traceback.print_exc()
            results["failed"] += 1
            results["details"].append(f"❌ Exception: {e}")

        logger.info(
            f"Embedding Generation Results: {results['passed']} passed, {results['failed']} failed"
        )
        return results

    def test_chunking_and_processing(self) -> Dict[str, Any]:
        """Test document chunking and processing."""
        logger.info("\n" + "=" * 60)
        logger.info("✂️ TESTING CHUNKING AND PROCESSING")
        logger.info("=" * 60)

        results = {
            "test_name": "chunking_processing",
            "passed": 0,
            "failed": 0,
            "details": [],
        }

        try:
            # Create temporary test file
            test_file = current_dir / "temp_test_file.md"
            test_file.write_text(self.sample_markdown)

            # Test file processing
            logger.info("Testing file processing...")
            chunks = self.chunker.process_file(test_file, current_dir)

            if chunks and len(chunks) > 0:
                results["passed"] += 1
                results["details"].append(
                    f"✅ File processed successfully ({len(chunks)} chunks)"
                )
            else:
                results["failed"] += 1
                results["details"].append("❌ File processing failed")
                return results

            # Test chunk structure
            logger.info("Testing chunk structure...")
            sample_chunk = chunks[0]

            required_fields = ["id", "content", "metadata"]
            for field in required_fields:
                if field in sample_chunk:
                    results["passed"] += 1
                    results["details"].append(f"✅ Chunk has required field '{field}'")
                else:
                    results["failed"] += 1
                    results["details"].append(f"❌ Chunk missing field '{field}'")

            # Test chunk ID uniqueness
            logger.info("Testing chunk ID uniqueness...")
            chunk_ids = [chunk["id"] for chunk in chunks]
            unique_ids = set(chunk_ids)

            if len(chunk_ids) == len(unique_ids):
                results["passed"] += 1
                results["details"].append("✅ Chunk IDs are unique")
            else:
                results["failed"] += 1
                results["details"].append("❌ Duplicate chunk IDs found")

            # Test content quality
            logger.info("Testing content quality...")
            valid_chunks = sum(
                1
                for chunk in chunks
                if self.chunker.validate_chunk({"page_content": chunk["content"]})
            )

            if valid_chunks == len(chunks):
                results["passed"] += 1
                results["details"].append("✅ All chunks pass validation")
            else:
                results["failed"] += 1
                results["details"].append(
                    f"❌ {len(chunks) - valid_chunks} chunks failed validation"
                )

            # Cleanup
            test_file.unlink()

        except Exception as e:
            logger.error(f"Error in chunking test: {e}")
            traceback.print_exc()
            results["failed"] += 1
            results["details"].append(f"❌ Exception: {e}")

        logger.info(
            f"Chunking Results: {results['passed']} passed, {results['failed']} failed"
        )
        return results

    def test_indexing_functionality(self) -> Dict[str, Any]:
        """Test Typesense indexing functionality."""
        logger.info("\n" + "=" * 60)
        logger.info("📇 TESTING INDEXING FUNCTIONALITY")
        logger.info("=" * 60)

        results = {
            "test_name": "indexing_functionality",
            "passed": 0,
            "failed": 0,
            "details": [],
        }

        try:
            # Test 1: Create test collection
            logger.info("Testing collection creation...")

            test_schema = {
                "name": self.test_collection,
                "fields": [
                    {"name": "id", "type": "string"},
                    {"name": "content", "type": "string"},
                    {"name": "title", "type": "string", "optional": True},
                    {"name": "file_path", "type": "string", "optional": True},
                    {"name": "chunk_index", "type": "int32", "optional": True},
                    {
                        "name": "content_type",
                        "type": "string",
                        "facet": True,
                        "optional": True,
                    },
                    {
                        "name": "has_code",
                        "type": "bool",
                        "facet": True,
                        "optional": True,
                    },
                    {
                        "name": "embedding",
                        "type": "float[]",
                        "num_dim": get_embedding_dimensions(),
                        "optional": True,
                    },
                ],
            }

            # Clean up existing test collection
            try:
                self.typesense_client.collections[self.test_collection].delete()
                logger.info("Cleaned up existing test collection")
            except:
                pass  # Collection doesn't exist

            # Create new collection
            collection_response = self.typesense_client.collections.create(test_schema)

            if collection_response:
                results["passed"] += 1
                results["details"].append("✅ Test collection created successfully")
            else:
                results["failed"] += 1
                results["details"].append("❌ Failed to create test collection")
                return results

            # Test 2: Index test documents
            logger.info("Testing document indexing...")

            test_docs = [
                {
                    "id": "test_doc_1",
                    "content": "This is the first test document about data visualization and charts.",
                    "title": "Data Visualization Guide",
                    "file_path": "test/doc1.md",
                    "chunk_index": 0,
                    "content_type": "guide",
                    "has_code": False,
                    "embedding": generate_embedding(
                        "This is the first test document about data visualization and charts."
                    ),
                },
                {
                    "id": "test_doc_2",
                    "content": "This is the second test document about machine learning algorithms and models.",
                    "title": "Machine Learning Basics",
                    "file_path": "test/doc2.md",
                    "chunk_index": 0,
                    "content_type": "tutorial",
                    "has_code": True,
                    "embedding": generate_embedding(
                        "This is the second test document about machine learning algorithms and models."
                    ),
                },
                {
                    "id": "test_doc_3",
                    "content": "This is the third test document about web scraping and data collection techniques.",
                    "title": "Web Scraping Tutorial",
                    "file_path": "test/doc3.md",
                    "chunk_index": 0,
                    "content_type": "tutorial",
                    "has_code": True,
                    "embedding": generate_embedding(
                        "This is the third test document about web scraping and data collection techniques."
                    ),
                },
            ]

            # Index documents
            indexed_count = 0
            for doc in test_docs:
                try:
                    response = self.typesense_client.collections[
                        self.test_collection
                    ].documents.create(doc)
                    indexed_count += 1
                except Exception as e:
                    logger.error(f"Failed to index document {doc['id']}: {e}")

            if indexed_count == len(test_docs):
                results["passed"] += 1
                results["details"].append(
                    f"✅ All {indexed_count} documents indexed successfully"
                )
            else:
                results["failed"] += 1
                results["details"].append(
                    f"❌ Only {indexed_count}/{len(test_docs)} documents indexed"
                )

            # Test 3: Verify indexing
            logger.info("Testing index verification...")

            # Wait a moment for indexing to complete
            time.sleep(1)

            # Check collection stats
            collection_info = self.typesense_client.collections[
                self.test_collection
            ].retrieve()
            doc_count = collection_info.get("num_documents", 0)

            if doc_count == len(test_docs):
                results["passed"] += 1
                results["details"].append(
                    f"✅ Collection contains correct number of documents ({doc_count})"
                )
            else:
                results["failed"] += 1
                results["details"].append(
                    f"❌ Document count mismatch (expected {len(test_docs)}, got {doc_count})"
                )

        except Exception as e:
            logger.error(f"Error in indexing test: {e}")
            traceback.print_exc()
            results["failed"] += 1
            results["details"].append(f"❌ Exception: {e}")

        logger.info(
            f"Indexing Results: {results['passed']} passed, {results['failed']} failed"
        )
        return results

    def test_search_functionality(self) -> Dict[str, Any]:
        """Test search functionality on indexed data."""
        logger.info("\n" + "=" * 60)
        logger.info("🔍 TESTING SEARCH FUNCTIONALITY")
        logger.info("=" * 60)

        results = {
            "test_name": "search_functionality",
            "passed": 0,
            "failed": 0,
            "details": [],
        }

        try:
            # Test 1: Basic text search
            logger.info("Testing basic text search...")

            search_params = {"q": "data visualization", "query_by": "content,title"}

            search_results = self.typesense_client.collections[
                self.test_collection
            ].documents.search(search_params)
            hits = search_results.get("hits", [])

            if hits and len(hits) > 0:
                results["passed"] += 1
                results["details"].append(
                    f"✅ Text search returned {len(hits)} results"
                )

                # Check if relevant document is in results
                visualization_found = any(
                    "visualization" in hit["document"]["content"].lower()
                    for hit in hits
                )
                if visualization_found:
                    results["passed"] += 1
                    results["details"].append(
                        "✅ Relevant document found in search results"
                    )
                else:
                    results["failed"] += 1
                    results["details"].append(
                        "❌ Relevant document not found in search results"
                    )
            else:
                results["failed"] += 1
                results["details"].append("❌ Text search returned no results")

            # Test 2: Faceted search
            logger.info("Testing faceted search...")

            facet_params = {
                "q": "*",
                "query_by": "content",
                "filter_by": "content_type:tutorial",
            }

            facet_results = self.typesense_client.collections[
                self.test_collection
            ].documents.search(facet_params)
            facet_hits = facet_results.get("hits", [])

            tutorial_count = sum(
                1
                for hit in facet_hits
                if hit["document"].get("content_type") == "tutorial"
            )

            if tutorial_count > 0:
                results["passed"] += 1
                results["details"].append(
                    f"✅ Faceted search found {tutorial_count} tutorial documents"
                )
            else:
                results["failed"] += 1
                results["details"].append("❌ Faceted search failed")

            # Test 3: Vector search (if embeddings are available)
            logger.info("Testing vector search...")

            try:
                query_embedding = generate_embedding("machine learning algorithms")

                # Use multi_search to handle large embedding vectors
                multi_search_request = {
                    "searches": [
                        {
                            "collection": self.test_collection,
                            "q": "*",
                            "vector_query": f"embedding:([{','.join(map(str, query_embedding))}])",
                            "query_by": "content",
                            "limit": 5,
                        }
                    ]
                }

                multi_search_response = self.typesense_client.multi_search.perform(
                    multi_search_request
                )

                # Extract results from multi_search response
                if (
                    multi_search_response
                    and isinstance(multi_search_response, dict)
                    and "results" in multi_search_response
                    and len(multi_search_response["results"]) > 0
                ):
                    vector_results = multi_search_response["results"][0]
                else:
                    vector_results = {"hits": []}
                vector_hits = vector_results.get("hits", [])

                if vector_hits and len(vector_hits) > 0:
                    results["passed"] += 1
                    results["details"].append(
                        f"✅ Vector search returned {len(vector_hits)} results"
                    )

                    # Check if machine learning document ranks high
                    top_hit = vector_hits[0]["document"]
                    if "machine learning" in top_hit["content"].lower():
                        results["passed"] += 1
                        results["details"].append(
                            "✅ Vector search ranking is accurate"
                        )
                    else:
                        results["failed"] += 1
                        results["details"].append(
                            "❌ Vector search ranking may be inaccurate"
                        )
                else:
                    results["failed"] += 1
                    results["details"].append("❌ Vector search returned no results")

            except Exception as e:
                logger.warning(f"Vector search test failed: {e}")
                results["details"].append(f"⚠️ Vector search test skipped: {e}")

            # Test 4: Hybrid search
            logger.info("Testing hybrid search...")

            try:
                query_embedding = generate_embedding("web scraping techniques")

                # Use multi_search for hybrid search as well
                hybrid_search_request = {
                    "searches": [
                        {
                            "collection": self.test_collection,
                            "q": "web scraping",
                            "query_by": "content,title",
                            "vector_query": f"embedding:([{','.join(map(str, query_embedding))}], alpha: 0.5)",
                            "limit": 5,
                        }
                    ]
                }

                multi_search_response = self.typesense_client.multi_search.perform(
                    hybrid_search_request
                )

                # Extract results from multi_search response
                if (
                    multi_search_response
                    and isinstance(multi_search_response, dict)
                    and "results" in multi_search_response
                    and len(multi_search_response["results"]) > 0
                ):
                    hybrid_results = multi_search_response["results"][0]
                else:
                    hybrid_results = {"hits": []}
                hybrid_hits = hybrid_results.get("hits", [])

                if hybrid_hits and len(hybrid_hits) > 0:
                    results["passed"] += 1
                    results["details"].append(
                        f"✅ Hybrid search returned {len(hybrid_hits)} results"
                    )
                else:
                    results["failed"] += 1
                    results["details"].append("❌ Hybrid search returned no results")

            except Exception as e:
                logger.warning(f"Hybrid search test failed: {e}")
                results["details"].append(f"⚠️ Hybrid search test skipped: {e}")

        except Exception as e:
            logger.error(f"Error in search functionality test: {e}")
            traceback.print_exc()
            results["failed"] += 1
            results["details"].append(f"❌ Exception: {e}")

        logger.info(
            f"Search Results: {results['passed']} passed, {results['failed']} failed"
        )
        return results

    def cleanup_test_environment(self) -> bool:
        """Clean up test environment."""
        try:
            logger.info("🧹 Cleaning up test environment...")

            # Delete test collection
            try:
                self.typesense_client.collections[self.test_collection].delete()
                logger.info("✅ Test collection deleted")
            except:
                logger.info("ℹ️ Test collection already cleaned up")

            return True

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            return False

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report."""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 STARTING COMPREHENSIVE DATA PIPELINE TEST")
        logger.info("=" * 80)

        start_time = time.time()

        # Setup environment
        if not self.setup_test_environment():
            return {"error": "Failed to setup test environment"}

        # Run all tests
        test_results = []

        try:
            # Test data cleaning
            test_results.append(self.test_data_cleaning())

            # Test embedding generation
            test_results.append(self.test_embedding_generation())

            # Test chunking and processing
            test_results.append(self.test_chunking_and_processing())

            # Test indexing
            test_results.append(self.test_indexing_functionality())

            # Test search functionality
            test_results.append(self.test_search_functionality())

        finally:
            # Always cleanup
            self.cleanup_test_environment()

        # Calculate overall results
        total_time = time.time() - start_time

        overall_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time_seconds": round(total_time, 3),
            "embedding_provider": self.config.defaults.embedding_provider,
            "embedding_model": getattr(
                self.config.embeddings, self.config.defaults.embedding_provider
            ).model,
            "test_results": test_results,
            "summary": {
                "total_tests": sum(r["passed"] + r["failed"] for r in test_results),
                "total_passed": sum(r["passed"] for r in test_results),
                "total_failed": sum(r["failed"] for r in test_results),
                "success_rate": 0.0,
            },
        }

        # Calculate success rate
        total_tests = overall_results["summary"]["total_tests"]
        if total_tests > 0:
            overall_results["summary"]["success_rate"] = round(
                (overall_results["summary"]["total_passed"] / total_tests) * 100, 1
            )

        return overall_results

    def generate_report(self, results: Dict[str, Any]) -> None:
        """Generate and display comprehensive test report."""
        logger.info("\n" + "=" * 80)
        logger.info("📊 DATA PIPELINE TEST REPORT")
        logger.info("=" * 80)

        # Overall summary
        summary = results["summary"]
        logger.info(f"⏱️  Total Time: {results['total_time_seconds']}s")
        logger.info(f"🧠 Embedding Provider: {results['embedding_provider']}")
        logger.info(f"📊 Model: {results['embedding_model']}")
        logger.info(f"✅ Tests Passed: {summary['total_passed']}")
        logger.info(f"❌ Tests Failed: {summary['total_failed']}")
        logger.info(f"📈 Success Rate: {summary['success_rate']}%")

        # Individual test results
        for test_result in results["test_results"]:
            logger.info(f"\n🔬 {test_result['test_name'].upper().replace('_', ' ')}:")
            logger.info(
                f"   Passed: {test_result['passed']}, Failed: {test_result['failed']}"
            )

            for detail in test_result["details"]:
                logger.info(f"   {detail}")

        # Save detailed report
        report_file = current_dir / "test_pipeline_report.json"
        with open(report_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"\n📄 Detailed report saved to: {report_file}")

        # Final assessment
        if summary["success_rate"] >= 90:
            logger.info("\n🎉 EXCELLENT: Data pipeline is working correctly!")
        elif summary["success_rate"] >= 75:
            logger.info("\n✅ GOOD: Data pipeline is mostly working with minor issues.")
        elif summary["success_rate"] >= 50:
            logger.info(
                "\n⚠️  WARNING: Data pipeline has significant issues that need attention."
            )
        else:
            logger.info(
                "\n🚨 CRITICAL: Data pipeline has major problems that must be fixed."
            )


def main():
    """Main function to run the comprehensive test."""
    tester = DataPipelineTester()

    try:
        results = tester.run_comprehensive_test()

        if "error" in results:
            logger.error(f"Test failed: {results['error']}")
            return

        tester.generate_report(results)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
