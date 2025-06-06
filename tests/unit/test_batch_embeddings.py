#!/usr/bin/env python3
"""
Comprehensive Test Suite for Batch Embedding Functions

This script tests all the new batch embedding functionality added to OptimizedRAGPipeline:
- Single embedding generation
- Batch embedding generation
- Streaming embedding generation
- Embeddings with metadata
- Embedding validation
- Save/load functionality

Usage:
    python test_batch_embeddings.py
"""

import json
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict
import numpy as np

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
    handlers=[
        logging.FileHandler("test_batch_embeddings.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class BatchEmbeddingTester:
    """Test suite for batch embedding functionality."""

    def __init__(self):
        """Initialize the tester with pipeline."""
        self.pipeline = OptimizedRAGPipeline()
        self.test_texts = [
            "Machine learning is a powerful tool for data analysis.",
            "Natural language processing enables computers to understand human language.",
            "Deep learning uses neural networks with multiple layers.",
            "Data visualization helps in understanding complex datasets.",
            "Python is a popular programming language for data science.",
            "Statistical analysis provides insights from data.",
            "Artificial intelligence mimics human cognitive functions.",
            "Big data refers to extremely large datasets.",
            "Cloud computing provides scalable computing resources.",
            "Database management systems store and retrieve data efficiently.",
        ]
        self.results = {}

    def test_single_embedding(self) -> bool:
        """Test single embedding generation."""
        logger.info("=== Testing Single Embedding Generation ===")

        try:
            test_text = "This is a test sentence for single embedding generation."

            start_time = time.time()
            embedding = self.pipeline.generate_embedding_single(test_text)
            duration = time.time() - start_time

            # Validate results
            expected_dims = self.pipeline.embedding_config["dimensions"]

            success = (
                isinstance(embedding, list)
                and len(embedding) == expected_dims
                and all(isinstance(x, (int, float)) for x in embedding)
            )

            self.results["single_embedding"] = {
                "success": success,
                "duration": duration,
                "dimensions": len(embedding),
                "expected_dimensions": expected_dims,
                "sample_values": embedding[:5] if len(embedding) >= 5 else embedding,
            }

            logger.info(f"Single embedding test: {'PASSED' if success else 'FAILED'}")
            logger.info(f"Duration: {duration:.3f}s, Dimensions: {len(embedding)}")

            return success

        except Exception as e:
            logger.error(f"Single embedding test failed: {e}")
            self.results["single_embedding"] = {"success": False, "error": str(e)}
            return False

    def test_batch_embedding(self) -> bool:
        """Test batch embedding generation."""
        logger.info("=== Testing Batch Embedding Generation ===")

        try:
            start_time = time.time()
            embeddings = self.pipeline.generate_embeddings_batch(
                self.test_texts, batch_size=5, show_progress=True, validate_inputs=True
            )
            duration = time.time() - start_time

            # Validate results
            expected_dims = self.pipeline.embedding_config["dimensions"]

            success = (
                isinstance(embeddings, list)
                and len(embeddings) == len(self.test_texts)
                and all(isinstance(emb, list) for emb in embeddings)
                and all(len(emb) == expected_dims for emb in embeddings)
            )

            self.results["batch_embedding"] = {
                "success": success,
                "duration": duration,
                "total_texts": len(self.test_texts),
                "total_embeddings": len(embeddings),
                "avg_time_per_text": duration / len(self.test_texts),
                "sample_embedding_length": len(embeddings[0]) if embeddings else 0,
            }

            logger.info(f"Batch embedding test: {'PASSED' if success else 'FAILED'}")
            logger.info(f"Duration: {duration:.3f}s for {len(self.test_texts)} texts")
            logger.info(f"Average: {duration/len(self.test_texts):.3f}s per text")

            return success

        except Exception as e:
            logger.error(f"Batch embedding test failed: {e}")
            self.results["batch_embedding"] = {"success": False, "error": str(e)}
            return False

    def test_streaming_embedding(self) -> bool:
        """Test streaming embedding generation."""
        logger.info("=== Testing Streaming Embedding Generation ===")

        try:
            # Create a larger test dataset
            large_test_texts = self.test_texts * 3  # 30 texts total

            start_time = time.time()
            embeddings = self.pipeline.generate_embeddings_streaming(
                large_test_texts, chunk_size=8, delay_between_chunks=0.1
            )
            duration = time.time() - start_time

            # Validate results
            expected_dims = self.pipeline.embedding_config["dimensions"]

            success = (
                isinstance(embeddings, list)
                and len(embeddings) == len(large_test_texts)
                and all(isinstance(emb, list) for emb in embeddings)
                and all(len(emb) == expected_dims for emb in embeddings)
            )

            self.results["streaming_embedding"] = {
                "success": success,
                "duration": duration,
                "total_texts": len(large_test_texts),
                "total_embeddings": len(embeddings),
                "chunk_size": 8,
                "avg_time_per_text": duration / len(large_test_texts),
            }

            logger.info(
                f"Streaming embedding test: {'PASSED' if success else 'FAILED'}"
            )
            logger.info(f"Duration: {duration:.3f}s for {len(large_test_texts)} texts")

            return success

        except Exception as e:
            logger.error(f"Streaming embedding test failed: {e}")
            self.results["streaming_embedding"] = {"success": False, "error": str(e)}
            return False

    def test_embeddings_with_metadata(self) -> bool:
        """Test embeddings with metadata generation."""
        logger.info("=== Testing Embeddings with Metadata ===")

        try:
            # Create metadata for each text
            metadata = [
                {"category": "ml", "difficulty": "medium", "words": len(text.split())}
                for text in self.test_texts
            ]

            start_time = time.time()
            results = self.pipeline.generate_embeddings_with_metadata(
                self.test_texts, metadata=metadata, batch_size=5
            )
            duration = time.time() - start_time

            # Validate results
            expected_dims = self.pipeline.embedding_config["dimensions"]

            success = (
                isinstance(results, list)
                and len(results) == len(self.test_texts)
                and all(isinstance(result, dict) for result in results)
                and all(
                    "embedding" in result and "text" in result and "metadata" in result
                    for result in results
                )
                and all(len(result["embedding"]) == expected_dims for result in results)
            )

            self.results["metadata_embedding"] = {
                "success": success,
                "duration": duration,
                "total_results": len(results),
                "sample_result_keys": list(results[0].keys()) if results else [],
                "sample_metadata": results[0]["metadata"] if results else {},
            }

            logger.info(f"Metadata embedding test: {'PASSED' if success else 'FAILED'}")
            logger.info(f"Duration: {duration:.3f}s")

            return success

        except Exception as e:
            logger.error(f"Metadata embedding test failed: {e}")
            self.results["metadata_embedding"] = {"success": False, "error": str(e)}
            return False

    def test_embedding_validation(self) -> bool:
        """Test embedding validation functionality."""
        logger.info("=== Testing Embedding Validation ===")

        try:
            # Generate some embeddings
            embeddings = self.pipeline.generate_embeddings_batch(self.test_texts[:5])

            # Test validation
            validation_results = self.pipeline.validate_embeddings(embeddings)

            # Validate the validation results
            success = (
                isinstance(validation_results, dict)
                and "valid" in validation_results
                and "total_embeddings" in validation_results
                and "expected_dimensions" in validation_results
                and validation_results["total_embeddings"] == len(embeddings)
            )

            self.results["embedding_validation"] = {
                "success": success,
                "validation_results": validation_results,
            }

            logger.info(
                f"Embedding validation test: {'PASSED' if success else 'FAILED'}"
            )
            logger.info(f"Validation results: {validation_results}")

            return success

        except Exception as e:
            logger.error(f"Embedding validation test failed: {e}")
            self.results["embedding_validation"] = {"success": False, "error": str(e)}
            return False

    def test_save_load_functionality(self) -> bool:
        """Test save and load embedding functionality."""
        logger.info("=== Testing Save/Load Functionality ===")

        try:
            # Generate embeddings
            embeddings = self.pipeline.generate_embeddings_batch(self.test_texts[:5])
            metadata = [{"index": i} for i in range(5)]

            # Test JSON format
            json_path = "test_embeddings.json"
            save_success = self.pipeline.save_embeddings_to_file(
                embeddings, self.test_texts[:5], json_path, metadata, format="json"
            )

            if save_success:
                loaded_data = self.pipeline.load_embeddings_from_file(
                    json_path, format="json"
                )
                load_success = (
                    isinstance(loaded_data, dict)
                    and "embeddings" in loaded_data
                    and "texts" in loaded_data
                    and len(loaded_data["embeddings"]) == len(embeddings)
                )
            else:
                load_success = False

            # Test JSONL format
            jsonl_path = "test_embeddings.jsonl"
            save_jsonl_success = self.pipeline.save_embeddings_to_file(
                embeddings, self.test_texts[:5], jsonl_path, metadata, format="jsonl"
            )

            if save_jsonl_success:
                loaded_jsonl_data = self.pipeline.load_embeddings_from_file(
                    jsonl_path, format="jsonl"
                )
                load_jsonl_success = (
                    isinstance(loaded_jsonl_data, dict)
                    and "embeddings" in loaded_jsonl_data
                    and "texts" in loaded_jsonl_data
                    and len(loaded_jsonl_data["embeddings"]) == len(embeddings)
                )
            else:
                load_jsonl_success = False

            success = (
                save_success
                and load_success
                and save_jsonl_success
                and load_jsonl_success
            )

            self.results["save_load"] = {
                "success": success,
                "json_save": save_success,
                "json_load": load_success,
                "jsonl_save": save_jsonl_success,
                "jsonl_load": load_jsonl_success,
            }

            logger.info(f"Save/Load test: {'PASSED' if success else 'FAILED'}")
            logger.info(f"JSON: Save={save_success}, Load={load_success}")
            logger.info(f"JSONL: Save={save_jsonl_success}, Load={load_jsonl_success}")

            # Cleanup test files
            for file_path in [json_path, jsonl_path]:
                try:
                    Path(file_path).unlink(missing_ok=True)
                except:
                    pass

            return success

        except Exception as e:
            logger.error(f"Save/Load test failed: {e}")
            self.results["save_load"] = {"success": False, "error": str(e)}
            return False

    def test_performance_comparison(self) -> bool:
        """Test performance comparison between different methods."""
        logger.info("=== Testing Performance Comparison ===")

        try:
            test_sizes = [10, 25, 50]
            performance_results = {}

            for size in test_sizes:
                test_data = self.test_texts * (size // len(self.test_texts) + 1)
                test_data = test_data[:size]

                logger.info(f"Testing with {size} texts...")

                # Test individual calls
                start_time = time.time()
                individual_embeddings = []
                for text in test_data:
                    embedding = self.pipeline.generate_embedding_single(text)
                    individual_embeddings.append(embedding)
                individual_duration = time.time() - start_time

                # Test batch processing
                start_time = time.time()
                batch_embeddings = self.pipeline.generate_embeddings_batch(test_data)
                batch_duration = time.time() - start_time

                # Test streaming
                start_time = time.time()
                streaming_embeddings = self.pipeline.generate_embeddings_streaming(
                    test_data, chunk_size=10, delay_between_chunks=0.05
                )
                streaming_duration = time.time() - start_time

                performance_results[f"size_{size}"] = {
                    "individual_duration": individual_duration,
                    "batch_duration": batch_duration,
                    "streaming_duration": streaming_duration,
                    "individual_per_text": individual_duration / size,
                    "batch_per_text": batch_duration / size,
                    "streaming_per_text": streaming_duration / size,
                    "batch_speedup": (
                        individual_duration / batch_duration
                        if batch_duration > 0
                        else 0
                    ),
                    "streaming_speedup": (
                        individual_duration / streaming_duration
                        if streaming_duration > 0
                        else 0
                    ),
                }

                logger.info(
                    f"Size {size} - Individual: {individual_duration:.3f}s, "
                    f"Batch: {batch_duration:.3f}s, Streaming: {streaming_duration:.3f}s"
                )
                logger.info(
                    f"Batch speedup: {performance_results[f'size_{size}']['batch_speedup']:.2f}x"
                )

            self.results["performance_comparison"] = {
                "success": True,
                "results": performance_results,
            }

            logger.info("Performance comparison test: PASSED")
            return True

        except Exception as e:
            logger.error(f"Performance comparison test failed: {e}")
            self.results["performance_comparison"] = {"success": False, "error": str(e)}
            return False

    def run_all_tests(self) -> Dict:
        """Run all batch embedding tests."""
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE BATCH EMBEDDING TESTS")
        logger.info("=" * 60)

        test_methods = [
            self.test_single_embedding,
            self.test_batch_embedding,
            self.test_streaming_embedding,
            self.test_embeddings_with_metadata,
            self.test_embedding_validation,
            self.test_save_load_functionality,
            self.test_performance_comparison,
        ]

        passed_tests = 0
        total_tests = len(test_methods)

        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed with exception: {e}")

        # Generate summary
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "overall_success": passed_tests == total_tests,
            "detailed_results": self.results,
        }

        logger.info("=" * 60)
        logger.info("BATCH EMBEDDING TESTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(
            f"Overall Result: {'PASSED' if summary['overall_success'] else 'FAILED'}"
        )

        return summary


def main():
    """Main function to run the batch embedding tests."""
    try:
        tester = BatchEmbeddingTester()
        results = tester.run_all_tests()

        # Save results to file
        output_file = Path("batch_embedding_test_results.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Test results saved to: {output_file}")

        # Return appropriate exit code
        sys.exit(0 if results["overall_success"] else 1)

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
