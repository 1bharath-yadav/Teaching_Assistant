#!/usr/bin/env python3
"""
Complete RAG Pipeline Runner

This script orchestrates the complete RAG pipeline:
1. Clone/update the tools-in-data-science-public repository
2. Process and chunk the markdown files
3. Generate embeddings for all content
4. Index everything into Typesense
5. Create unified collections for search

Usage:
    python run_rag_pipeline.py --help
    python run_rag_pipeline.py --full-pipeline
    python run_rag_pipeline.py --chapters-only
    python run_rag_pipeline.py --discourse-only
    python run_rag_pipeline.py --test-search "machine learning"
"""

import argparse
import sys
import logging
from pathlib import Path
import subprocess
import time

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import our modules
from optimized_chunker import OptimizedChunker
from optimized_rag_pipeline import OptimizedRAGPipeline
from lib.config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("rag_pipeline_runner.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def clone_or_update_repository() -> bool:
    """Clone or update the tools-in-data-science-public repository."""
    config = get_config()
    repo_url = config.chapters.repository_url
    repo_path = Path(config.chapters.local_path)

    if repo_path.exists():
        logger.info("Repository exists, updating...")
        try:
            subprocess.run(
                ["git", "-C", str(repo_path), "pull", "origin", "main"],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Repository updated successfully!")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to update repository: {e}")
            logger.info("Continuing with existing repository...")
            return True
    else:
        logger.info(f"Cloning repository from {repo_url}...")
        repo_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.run(
                ["git", "clone", repo_url, str(repo_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Repository cloned successfully!")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            return False


def run_chunking_pipeline() -> bool:
    """Run the optimized chunking pipeline."""
    logger.info("=" * 50)
    logger.info("STARTING CHUNKING PIPELINE")
    logger.info("=" * 50)

    chunker = OptimizedChunker()
    success = chunker.process_repository()

    if success:
        logger.info("Chunking pipeline completed successfully!")
    else:
        logger.error("Chunking pipeline failed!")

    return success


def run_embedding_pipeline(
    process_discourse: bool = True, process_chapters: bool = True
) -> bool:
    """Run the optimized embedding and indexing pipeline."""
    logger.info("=" * 50)
    logger.info("STARTING EMBEDDING & INDEXING PIPELINE")
    logger.info("=" * 50)

    pipeline = OptimizedRAGPipeline()

    success = True

    try:
        if process_discourse:
            logger.info("Processing discourse data...")
            discourse_success = pipeline.process_discourse_data()
            if not discourse_success:
                logger.warning("Discourse processing failed, continuing...")
                success = False

        if process_chapters:
            logger.info("Processing chapters data...")
            chapters_success = pipeline.process_chapters_data()
            if not chapters_success:
                logger.warning("Chapters processing failed, continuing...")
                success = False

        if process_discourse or process_chapters:
            logger.info("Creating unified collection...")
            pipeline.create_unified_collection()

        # Print final metrics
        pipeline.metrics.end_time = time.time()
        logger.info("=" * 50)
        logger.info("PIPELINE METRICS")
        logger.info("=" * 50)
        logger.info(pipeline.metrics.summary())

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        success = False

    return success


def test_search_functionality(queries: list = None) -> None:
    """Test the search functionality with sample queries."""
    logger.info("=" * 50)
    logger.info("TESTING SEARCH FUNCTIONALITY")
    logger.info("=" * 50)

    if queries is None:
        queries = [
            "data visualization techniques",
            "machine learning models",
            "project deployment strategies",
            "data preparation methods",
            "development tools for data science",
        ]

    pipeline = OptimizedRAGPipeline()

    for query in queries:
        logger.info(f"\n🔍 Testing query: '{query}'")
        logger.info("-" * 40)

        try:
            results = pipeline.test_search(query)

            if results:
                logger.info(f"Found {len(results)} results:")
                for i, result in enumerate(results[:3], 1):
                    logger.info(
                        f"  {i}. [{result['source']}] {result['content'][:100]}..."
                    )
                    if result.get("module"):
                        logger.info(f"     Module: {result['module']}")
                    if result.get("topic_title"):
                        logger.info(f"     Topic: {result['topic_title']}")
            else:
                logger.warning(f"No results found for query: '{query}'")

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")


def validate_configuration() -> bool:
    """Validate the configuration before running pipeline."""
    logger.info("Validating configuration...")

    try:
        config = get_config()

        # Check embedding provider
        provider = config.embeddings.provider
        logger.info(f"Embedding provider: {provider}")

        if provider == "openai":
            if (
                not config.openai.api_key
                or config.openai.api_key == "your-openai-api-key-here"
            ):
                logger.error("OpenAI API key not configured!")
                return False
        elif provider == "ollama":
            # Test Ollama connection
            import requests

            try:
                # Remove /v1 suffix if present for health check
                base_url = config.ollama.base_url.rstrip("/v1")
                response = requests.get(f"{base_url}/api/version", timeout=5)
                if response.status_code != 200:
                    logger.error("Ollama server not accessible!")
                    return False
                logger.info("Ollama server connection verified")
            except Exception as e:
                logger.error(f"Failed to connect to Ollama: {e}")
                return False

        # Check Typesense connection
        try:
            import typesense

            client = typesense.Client(
                {
                    "nodes": [
                        {
                            "host": config.typesense.nodes[0].host,
                            "port": str(config.typesense.nodes[0].port),
                            "protocol": config.typesense.nodes[0].protocol,
                        }
                    ],
                    "api_key": config.typesense.api_key,
                    "connection_timeout_seconds": 5,
                }
            )

            # Test connection
            health = client.operations.is_healthy()
            if not health:
                logger.error("Typesense server not healthy!")
                return False
            logger.info("Typesense server connection verified")

        except Exception as e:
            logger.error(f"Failed to connect to Typesense: {e}")
            return False

        logger.info("Configuration validation passed!")
        return True

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Run the complete RAG pipeline")
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Run the complete pipeline (clone, chunk, embed, index)",
    )
    parser.add_argument(
        "--chapters-only", action="store_true", help="Process only chapter data"
    )
    parser.add_argument(
        "--discourse-only", action="store_true", help="Process only discourse data"
    )
    parser.add_argument(
        "--chunking-only", action="store_true", help="Run only the chunking pipeline"
    )
    parser.add_argument(
        "--embedding-only", action="store_true", help="Run only the embedding pipeline"
    )
    parser.add_argument(
        "--test-search", type=str, nargs="*", help="Test search with specific queries"
    )
    parser.add_argument(
        "--validate-config", action="store_true", help="Validate configuration only"
    )
    parser.add_argument(
        "--skip-validation", action="store_true", help="Skip configuration validation"
    )

    args = parser.parse_args()

    # Show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return

    logger.info("=" * 60)
    logger.info("OPTIMIZED RAG PIPELINE RUNNER")
    logger.info("=" * 60)

    # Validate configuration unless skipped
    if not args.skip_validation:
        if not validate_configuration():
            logger.error(
                "Configuration validation failed! Use --skip-validation to bypass."
            )
            sys.exit(1)

    start_time = time.time()

    try:
        if args.validate_config:
            logger.info("Configuration validation completed successfully!")
            return

        if args.test_search is not None:
            queries = args.test_search if args.test_search else None
            test_search_functionality(queries)
            return

        if args.full_pipeline:
            # Run complete pipeline
            logger.info("Running FULL RAG pipeline...")

            # Step 1: Clone/update repository
            if not clone_or_update_repository():
                logger.error("Failed to clone/update repository!")
                sys.exit(1)

            # Step 2: Run chunking
            if not run_chunking_pipeline():
                logger.error("Chunking pipeline failed!")
                sys.exit(1)

            # Step 3: Run embedding and indexing
            if not run_embedding_pipeline():
                logger.error("Embedding pipeline failed!")
                sys.exit(1)

            # Step 4: Test search
            test_search_functionality()

        elif args.chunking_only:
            if not clone_or_update_repository():
                logger.error("Failed to clone/update repository!")
                sys.exit(1)
            if not run_chunking_pipeline():
                sys.exit(1)

        elif args.embedding_only:
            if not run_embedding_pipeline():
                sys.exit(1)

        elif args.chapters_only:
            if not clone_or_update_repository():
                logger.error("Failed to clone/update repository!")
                sys.exit(1)
            if not run_chunking_pipeline():
                logger.error("Chunking failed!")
                sys.exit(1)
            if not run_embedding_pipeline(
                process_discourse=False, process_chapters=True
            ):
                sys.exit(1)

        elif args.discourse_only:
            if not run_embedding_pipeline(
                process_discourse=True, process_chapters=False
            ):
                sys.exit(1)

        elapsed_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY in {elapsed_time:.2f} seconds!")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
