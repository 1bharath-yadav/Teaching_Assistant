#!/usr/bin/env python3
"""
Optimized RAG Data Ingestion Pipeline

This script provides a complete, optimized pipeline for processing the tools-in-data-science-public
repository and discourse data into embeddings and indexing them into Typesense.

Features:
- Unified configuration management using config.yaml
- Support for both Ollama and OpenAI embedding providers
- Batch processing for efficient embedding generation
- Robust error handling and logging
- Data validation and cleaning
- Optimized Typesense schemas
- Progress tracking and metrics
- Resume capability for interrupted processing
"""

import json
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import hashlib
import os
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import re
import requests

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import configuration modules
from lib.config import get_config
import typesense
from typesense.exceptions import ObjectNotFound, ObjectAlreadyExists

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("rag_pipeline.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Handles embedding generation for different providers."""

    def __init__(self, config):
        self.config = config
        self.provider = config.embeddings.provider
        self.embedding_config = self._get_embedding_config()

    def _get_embedding_config(self) -> Dict:
        """Get embedding configuration based on provider."""
        if self.provider == "openai":
            return {
                "provider": "openai",
                "model": self.config.embeddings.openai.model,
                "dimensions": self.config.embeddings.openai.dimensions,
                "api_key": self.config.openai.api_key,
                "base_url": self.config.openai.base_url,
            }
        elif self.provider == "ollama":
            return {
                "provider": "ollama",
                "model": self.config.embeddings.ollama.model,
                "dimensions": self.config.embeddings.ollama.dimensions,
                "base_url": self.config.ollama.base_url,
                "api_key": self.config.ollama.api_key,
            }
        elif self.provider == "azure":
            return {
                "provider": "azure",
                "model": self.config.embeddings.azure.model,
                "dimensions": self.config.embeddings.azure.dimensions,
                "api_key": self.config.azure.api_key,
                "base_url": self.config.azure.base_url,
                "api_version": self.config.azure.api_version,
            }
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def generate_embeddings(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        logger.info(
            f"Generating embeddings for {len(texts)} texts using {self.provider}"
        )

        all_embeddings = []

        # Process in batches to avoid API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = self._generate_batch_embeddings(batch)
            all_embeddings.extend(batch_embeddings)

            if i + batch_size < len(texts):
                time.sleep(0.1)  # Small delay between batches

        return all_embeddings

    def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            if self.provider == "openai":
                return self._generate_openai_embeddings(texts)
            elif self.provider == "ollama":
                return self._generate_ollama_embeddings(texts)
            elif self.provider == "azure":
                return self._generate_azure_embeddings(texts)
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                return [[] for _ in texts]
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[] for _ in texts]

    def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        import openai

        client = openai.OpenAI(
            api_key=self.embedding_config["api_key"],
            base_url=self.embedding_config["base_url"],
        )

        response = client.embeddings.create(
            model=self.embedding_config["model"], input=texts
        )

        return [embedding.embedding for embedding in response.data]

    def _generate_ollama_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama API."""
        embeddings = []

        # Remove /v1 suffix if present for Ollama API
        base_url = self.embedding_config["base_url"].rstrip("/v1")

        for text in texts:
            response = requests.post(
                f"{base_url}/api/embeddings",
                json={"model": self.embedding_config["model"], "prompt": text},
            )

            if response.status_code == 200:
                embedding = response.json().get("embedding", [])
                embeddings.append(embedding)
            else:
                logger.warning(
                    f"Failed to generate embedding for text: {response.status_code}"
                )
                embeddings.append([])

        return embeddings

    def _generate_azure_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Azure OpenAI API."""
        import openai

        client = openai.AzureOpenAI(
            api_key=self.embedding_config["api_key"],
            api_version=self.embedding_config["api_version"],
            azure_endpoint=self.embedding_config["base_url"],
        )

        response = client.embeddings.create(
            model=self.embedding_config["model"], input=texts
        )

        return [embedding.embedding for embedding in response.data]


@dataclass
class ProcessingMetrics:
    """Track processing metrics and progress."""

    total_chunks: int = 0
    processed_chunks: int = 0
    failed_chunks: int = 0
    start_time: datetime = None
    end_time: datetime = None
    embedding_time: float = 0
    indexing_time: float = 0

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()

    def completion_rate(self) -> float:
        if self.total_chunks == 0:
            return 0.0
        return (self.processed_chunks / self.total_chunks) * 100

    def processing_speed(self) -> float:
        if not self.start_time:
            return 0.0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed == 0:
            return 0.0
        return self.processed_chunks / elapsed

    def summary(self) -> str:
        return f"""
Processing Summary:
- Total chunks: {self.total_chunks}
- Processed: {self.processed_chunks}
- Failed: {self.failed_chunks}
- Success rate: {((self.processed_chunks - self.failed_chunks) / max(1, self.total_chunks)) * 100:.1f}%
- Completion rate: {self.completion_rate():.1f}%
- Processing speed: {self.processing_speed():.2f} chunks/sec
- Embedding time: {self.embedding_time:.2f}s
- Indexing time: {self.indexing_time:.2f}s
"""


class OptimizedRAGPipeline:
    """Optimized RAG pipeline for data ingestion and embedding."""

    def __init__(self):
        """Initialize the pipeline with configuration."""
        self.config = get_config()
        self.client = self._get_typesense_client()
        self.embedding_provider = EmbeddingProvider(self.config)
        self.embedding_config = self.embedding_provider.embedding_config
        self.batch_size = getattr(self.config.discourse, "batch_size", 100)
        self.metrics = ProcessingMetrics()

        # Create processing directories
        self.output_dir = current_dir / "processed_output"
        self.output_dir.mkdir(exist_ok=True)

        logger.info(
            f"Initialized pipeline with embedding provider: {self.embedding_config['provider']}"
        )
        logger.info(f"Embedding model: {self.embedding_config['model']}")
        logger.info(f"Embedding dimensions: {self.embedding_config['dimensions']}")
        logger.info(f"Batch size: {self.batch_size}")

    # ========== DEDICATED BATCH EMBEDDING FUNCTIONS ==========

    def generate_embedding_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for single embedding generation")
            return [0.0] * self.embedding_config["dimensions"]

        try:
            # Use the existing embedding provider for single text
            embeddings = self.embedding_provider.generate_embeddings(
                [text.strip()], batch_size=1
            )
            return (
                embeddings[0]
                if embeddings
                else [0.0] * self.embedding_config["dimensions"]
            )
        except Exception as e:
            logger.error(f"Error generating single embedding: {e}")
            return [0.0] * self.embedding_config["dimensions"]

    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = True,
        validate_inputs: bool = True,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using optimized batch processing.

        Args:
            texts: List of texts to embed
            batch_size: Override default batch size for this operation
            show_progress: Whether to show progress logging
            validate_inputs: Whether to validate and clean input texts

        Returns:
            List of embedding vectors (list of lists of floats)
        """
        if not texts:
            logger.warning("Empty text list provided for batch embedding generation")
            return []

        # Use provided batch size or fall back to instance default
        effective_batch_size = batch_size or self.batch_size

        if show_progress:
            logger.info(
                f"Generating embeddings for {len(texts)} texts with batch size {effective_batch_size}"
            )

        # Validate and clean inputs if requested
        processed_texts = []
        indices = []

        if validate_inputs:
            for i, text in enumerate(texts):
                if text and text.strip() and len(text.strip()) >= 10:
                    processed_texts.append(text.strip())
                    indices.append(i)
                elif show_progress:
                    logger.debug(f"Skipping invalid text at index {i}")
        else:
            processed_texts = [text if text else "" for text in texts]
            indices = list(range(len(texts)))

        if not processed_texts:
            logger.warning("No valid texts found after filtering")
            return [[0.0] * self.embedding_config["dimensions"] for _ in texts]

        try:
            # Generate embeddings using the existing provider
            embeddings = self.embedding_provider.generate_embeddings(
                processed_texts, batch_size=effective_batch_size
            )

            # Reconstruct full results array matching input order
            if validate_inputs:
                result = []
                embedding_idx = 0
                for i in range(len(texts)):
                    if i in indices:
                        if (
                            embedding_idx < len(embeddings)
                            and embeddings[embedding_idx]
                        ):
                            result.append(embeddings[embedding_idx])
                        else:
                            result.append([0.0] * self.embedding_config["dimensions"])
                        embedding_idx += 1
                    else:
                        result.append([0.0] * self.embedding_config["dimensions"])
                return result
            else:
                return embeddings

        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            return [[0.0] * self.embedding_config["dimensions"] for _ in texts]

    def generate_embeddings_streaming(
        self, texts: List[str], chunk_size: int = 50, delay_between_chunks: float = 0.1
    ) -> List[List[float]]:
        """
        Generate embeddings with streaming/chunked approach for very large datasets.

        Args:
            texts: List of texts to embed
            chunk_size: Size of each processing chunk
            delay_between_chunks: Delay in seconds between chunks to avoid rate limits

        Returns:
            List of embedding vectors

        Yields:
            Progress updates during processing
        """
        if not texts:
            return []

        logger.info(
            f"Streaming embedding generation for {len(texts)} texts in chunks of {chunk_size}"
        )

        all_embeddings = []
        total_chunks = (len(texts) + chunk_size - 1) // chunk_size

        for i in range(0, len(texts), chunk_size):
            chunk = texts[i : i + chunk_size]
            chunk_num = i // chunk_size + 1

            logger.info(
                f"Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} texts)"
            )

            try:
                # Generate embeddings for this chunk
                chunk_embeddings = self.generate_embeddings_batch(
                    chunk,
                    batch_size=min(chunk_size, self.batch_size),
                    show_progress=False,
                    validate_inputs=True,
                )

                all_embeddings.extend(chunk_embeddings)

                # Progress update
                processed_count = len(all_embeddings)
                progress = (processed_count / len(texts)) * 100
                logger.info(
                    f"Streaming progress: {progress:.1f}% ({processed_count}/{len(texts)})"
                )

                # Delay between chunks if not the last chunk
                if i + chunk_size < len(texts) and delay_between_chunks > 0:
                    time.sleep(delay_between_chunks)

            except Exception as e:
                logger.error(f"Error processing chunk {chunk_num}: {e}")
                # Add zero embeddings for failed chunk
                failed_embeddings = [
                    [0.0] * self.embedding_config["dimensions"] for _ in chunk
                ]
                all_embeddings.extend(failed_embeddings)

        logger.info("Streaming embedding generation completed")
        return all_embeddings

    def generate_embeddings_with_metadata(
        self,
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
        batch_size: Optional[int] = None,
    ) -> List[Dict]:
        """
        Generate embeddings with associated metadata for each text.

        Args:
            texts: List of texts to embed
            metadata: Optional list of metadata dicts for each text
            batch_size: Override default batch size

        Returns:
            List of dicts containing 'embedding', 'text', and 'metadata' keys
        """
        if not texts:
            return []

        logger.info(f"Generating embeddings with metadata for {len(texts)} texts")

        # Generate embeddings
        embeddings = self.generate_embeddings_batch(texts, batch_size=batch_size)

        # Combine with metadata
        results = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            result = {
                "text": text,
                "embedding": embedding,
                "metadata": metadata[i] if metadata and i < len(metadata) else {},
                "embedding_dimensions": len(embedding),
                "text_length": len(text),
                "generated_at": datetime.now().isoformat(),
            }
            results.append(result)

        return results

    def validate_embeddings(self, embeddings: List[List[float]]) -> Dict[str, any]:
        """
        Validate embedding quality and consistency.

        Args:
            embeddings: List of embedding vectors to validate

        Returns:
            Dict with validation results and statistics
        """
        if not embeddings:
            return {"valid": False, "error": "No embeddings provided"}

        expected_dim = self.embedding_config["dimensions"]

        validation_results = {
            "total_embeddings": len(embeddings),
            "expected_dimensions": expected_dim,
            "valid_embeddings": 0,
            "invalid_embeddings": 0,
            "dimension_mismatches": 0,
            "zero_embeddings": 0,
            "average_magnitude": 0.0,
            "valid": True,
            "errors": [],
        }

        total_magnitude = 0.0

        for i, embedding in enumerate(embeddings):
            try:
                # Check if embedding exists and is a list
                if not isinstance(embedding, list):
                    validation_results["invalid_embeddings"] += 1
                    validation_results["errors"].append(f"Embedding {i}: Not a list")
                    continue

                # Check dimensions
                if len(embedding) != expected_dim:
                    validation_results["dimension_mismatches"] += 1
                    validation_results["errors"].append(
                        f"Embedding {i}: Expected {expected_dim} dimensions, got {len(embedding)}"
                    )
                    continue

                # Check for zero embeddings
                if all(x == 0.0 for x in embedding):
                    validation_results["zero_embeddings"] += 1
                    validation_results["errors"].append(f"Embedding {i}: All zeros")

                # Calculate magnitude
                magnitude = sum(x * x for x in embedding) ** 0.5
                total_magnitude += magnitude

                validation_results["valid_embeddings"] += 1

            except Exception as e:
                validation_results["invalid_embeddings"] += 1
                validation_results["errors"].append(f"Embedding {i}: Exception - {e}")

        # Calculate average magnitude
        if validation_results["valid_embeddings"] > 0:
            validation_results["average_magnitude"] = (
                total_magnitude / validation_results["valid_embeddings"]
            )

        # Overall validity
        validation_results["valid"] = (
            validation_results["valid_embeddings"] > 0
            and validation_results["dimension_mismatches"] == 0
            and validation_results["invalid_embeddings"] == 0
        )

        return validation_results

    def save_embeddings_to_file(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        output_path: str,
        metadata: Optional[List[Dict]] = None,
        format: str = "json",
    ) -> bool:
        """
        Save embeddings to file in various formats.

        Args:
            embeddings: List of embedding vectors
            texts: Original texts
            output_path: Path to save the embeddings
            metadata: Optional metadata for each embedding
            format: Output format ('json', 'jsonl', 'npz')

        Returns:
            True if successful, False otherwise
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if format.lower() == "json":
                # Save as JSON
                data = {
                    "embeddings": embeddings,
                    "texts": texts,
                    "metadata": metadata or [{}] * len(texts),
                    "config": {
                        "provider": self.embedding_config["provider"],
                        "model": self.embedding_config["model"],
                        "dimensions": self.embedding_config["dimensions"],
                        "generated_at": datetime.now().isoformat(),
                    },
                }

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            elif format.lower() == "jsonl":
                # Save as JSONL (one JSON object per line)
                with open(output_file, "w", encoding="utf-8") as f:
                    for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                        record = {
                            "id": i,
                            "text": text,
                            "embedding": embedding,
                            "metadata": (
                                metadata[i] if metadata and i < len(metadata) else {}
                            ),
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")

            elif format.lower() == "npz":
                # Save as NumPy compressed format
                import numpy as np

                np.savez_compressed(
                    output_file,
                    embeddings=np.array(embeddings),
                    texts=np.array(texts),
                    metadata=np.array(metadata or [{}] * len(texts)),
                )

            else:
                logger.error(f"Unsupported format: {format}")
                return False

            logger.info(
                f"Successfully saved {len(embeddings)} embeddings to {output_file}"
            )
            return True

        except Exception as e:
            logger.error(f"Error saving embeddings to {output_path}: {e}")
            return False

    def load_embeddings_from_file(self, input_path: str, format: str = "auto") -> Dict:
        """
        Load embeddings from file.

        Args:
            input_path: Path to the embeddings file
            format: Input format ('auto', 'json', 'jsonl', 'npz')

        Returns:
            Dict containing embeddings, texts, and metadata
        """
        try:
            input_file = Path(input_path)

            if not input_file.exists():
                logger.error(f"Embeddings file not found: {input_file}")
                return {}

            # Auto-detect format from extension
            if format == "auto":
                if input_file.suffix.lower() == ".json":
                    format = "json"
                elif input_file.suffix.lower() == ".jsonl":
                    format = "jsonl"
                elif input_file.suffix.lower() == ".npz":
                    format = "npz"
                else:
                    logger.error(f"Cannot auto-detect format for {input_file}")
                    return {}

            if format.lower() == "json":
                with open(input_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data

            elif format.lower() == "jsonl":
                texts = []
                embeddings = []
                metadata = []

                with open(input_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line.strip())
                            texts.append(record.get("text", ""))
                            embeddings.append(record.get("embedding", []))
                            metadata.append(record.get("metadata", {}))

                return {"texts": texts, "embeddings": embeddings, "metadata": metadata}

            elif format.lower() == "npz":
                import numpy as np

                data = np.load(input_file)
                return {
                    "embeddings": data["embeddings"].tolist(),
                    "texts": data["texts"].tolist(),
                    "metadata": data["metadata"].tolist(),
                }

            else:
                logger.error(f"Unsupported format: {format}")
                return {}

        except Exception as e:
            logger.error(f"Error loading embeddings from {input_path}: {e}")
            return {}

    # ========== END BATCH EMBEDDING FUNCTIONS ==========

    def _get_typesense_client(self) -> typesense.Client:
        """Get configured Typesense client."""
        typesense_config = self.config.typesense
        return typesense.Client(
            {
                "nodes": [
                    {
                        "host": typesense_config.nodes[0].host,
                        "port": str(typesense_config.nodes[0].port),
                        "protocol": typesense_config.nodes[0].protocol,
                    }
                ],
                "api_key": typesense_config.api_key,
                "connection_timeout_seconds": typesense_config.connection_timeout,
            }
        )

    def get_optimized_schema(self, collection_name: str, collection_type: str) -> Dict:
        """Get optimized Typesense schema based on collection type."""
        base_fields = [
            {"name": "id", "type": "string", "facet": False},
            {"name": "content", "type": "string", "facet": False},
            {
                "name": "embedding",
                "type": "float[]",
                "num_dim": self.embedding_config["dimensions"],
            },
        ]

        if collection_type == "discourse":
            additional_fields = [
                {"name": "topic_id", "type": "string", "facet": True},
                {"name": "topic_title", "type": "string", "facet": False},
                {"name": "url", "type": "string", "facet": False, "optional": True},
                {
                    "name": "timestamp",
                    "type": "string",
                    "facet": True,
                    "optional": True,
                },
                {"name": "username", "type": "string", "facet": True, "optional": True},
                {
                    "name": "post_number",
                    "type": "int32",
                    "facet": True,
                    "optional": True,
                },
                {"name": "has_code", "type": "bool", "facet": True, "optional": True},
                {
                    "name": "content_length",
                    "type": "int32",
                    "facet": True,
                    "optional": False,  # Cannot be optional as it's the default sorting field
                },
                {
                    "name": "clean_content",
                    "type": "string",
                    "facet": False,
                    "optional": True,
                },
            ]
        elif collection_type == "chapters":
            additional_fields = [
                {"name": "module", "type": "string", "facet": True, "optional": True},
                {
                    "name": "file_path",
                    "type": "string",
                    "facet": True,
                    "optional": True,
                },
                {
                    "name": "chunk_index",
                    "type": "int32",
                    "facet": True,
                    "optional": True,
                },
                {
                    "name": "content_type",
                    "type": "string",
                    "facet": True,
                    "optional": True,
                },
                {"name": "has_code", "type": "bool", "facet": True, "optional": True},
                {
                    "name": "content_length",
                    "type": "int32",
                    "facet": True,
                    "optional": False,  # Cannot be optional as it's the default sorting field
                },
            ]
        else:
            additional_fields = []

        schema = {
            "name": collection_name,
            "fields": base_fields + additional_fields,
            "default_sorting_field": "content_length",
        }

        return schema

    def create_or_update_collection(
        self, collection_name: str, collection_type: str
    ) -> bool:
        """Create or update Typesense collection with optimized schema."""
        schema = self.get_optimized_schema(collection_name, collection_type)

        try:
            # Check if collection exists
            existing = self.client.collections[collection_name].retrieve()
            logger.info(f"Collection '{collection_name}' already exists.")

            # Check if schema needs update (simplified check)
            existing_fields = {f["name"]: f for f in existing["fields"]}
            new_fields = {f["name"]: f for f in schema["fields"]}

            if existing_fields != new_fields:
                logger.info(
                    f"Schema differs, recreating collection '{collection_name}'"
                )
                self.client.collections[collection_name].delete()
                self.client.collections.create(schema)
                logger.info(f"Recreated collection '{collection_name}'")

        except ObjectNotFound:
            self.client.collections.create(schema)
            logger.info(f"Created new collection '{collection_name}'")

        return True

    def clean_text_content(self, content: str) -> Tuple[str, Dict]:
        """Clean and analyze text content."""
        import re

        # Remove HTML tags
        clean_content = re.sub(r"<[^>]+>", "", content)

        # Remove excessive whitespace
        clean_content = re.sub(r"\s+", " ", clean_content).strip()

        # Extract metadata
        metadata = {
            "has_code": bool(re.search(r"<code>|```|`[^`]+`", content)),
            "content_length": len(clean_content),
            "original_length": len(content),
        }

        return clean_content, metadata

    def validate_chunk(self, chunk: Dict) -> bool:
        """Validate chunk data quality."""
        if not chunk.get("content"):
            return False

        content = chunk["content"].strip()

        # Skip very short chunks
        if len(content) < 50:
            return False

        # Skip chunks that are mostly special characters
        alpha_ratio = sum(c.isalnum() for c in content) / len(content)
        if alpha_ratio < 0.3:
            return False

        return True

    def process_discourse_data(self, input_file: Optional[str] = None) -> bool:
        """Process discourse posts with optimized pipeline."""
        input_file = input_file or (current_dir / "discourse" / "scraped_posts.json")
        input_path = Path(input_file)

        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return False

        logger.info(f"Processing discourse data from: {input_path}")

        # Load discourse posts
        with open(input_path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        logger.info(f"Loaded {len(posts)} discourse posts")

        # Create collection
        collection_name = "discourse_posts_optimized"
        self.create_or_update_collection(collection_name, "discourse")

        # Process posts in batches
        processed_posts = []
        self.metrics.total_chunks = len(posts)

        for i in range(0, len(posts), self.batch_size):
            batch = posts[i : i + self.batch_size]
            processed_batch = self._process_discourse_batch(batch)
            processed_posts.extend(processed_batch)

            self.metrics.processed_chunks += len(processed_batch)
            logger.info(
                f"Processed batch {i//self.batch_size + 1}/{(len(posts) + self.batch_size - 1)//self.batch_size}"
            )
            logger.info(f"Progress: {self.metrics.completion_rate():.1f}%")

        # Generate embeddings in batches
        logger.info("Generating embeddings for discourse posts...")
        start_time = time.time()

        texts = [post["clean_content"] for post in processed_posts]
        embeddings = self.embedding_provider.generate_embeddings(
            texts, batch_size=self.batch_size
        )

        self.metrics.embedding_time += time.time() - start_time

        # Prepare final documents
        documents = []
        for post, embedding in zip(processed_posts, embeddings):
            if embedding:
                post["embedding"] = embedding
                documents.append(post)
            else:
                self.metrics.failed_chunks += 1

        # Index to Typesense
        logger.info(f"Indexing {len(documents)} discourse posts to Typesense...")
        start_time = time.time()

        self._batch_index_documents(collection_name, documents)

        self.metrics.indexing_time += time.time() - start_time

        # Save processed data
        output_file = self.output_dir / "processed_discourse_posts.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved processed discourse data to: {output_file}")
        return True

    def _process_discourse_batch(self, batch: List[Dict]) -> List[Dict]:
        """Process a batch of discourse posts."""
        processed = []

        for post in batch:
            try:
                # Clean content
                clean_content, metadata = self.clean_text_content(
                    post.get("post_content", "")
                )

                if not clean_content or len(clean_content) < 20:
                    continue

                # Create processed post
                processed_post = {
                    "id": f"discourse_{post.get('post_id', '')}",
                    "topic_id": str(post.get("topic_id", "")),
                    "topic_title": post.get("topic_title", ""),
                    "content": post.get("post_content", ""),
                    "clean_content": clean_content,
                    "url": f"https://discourse.example.com/t/{post.get('topic_id', '')}/{post.get('post_number', '')}",
                    "timestamp": post.get("created_at", ""),
                    "username": post.get("username", ""),
                    "post_number": post.get("post_number", 1),
                    **metadata,
                }

                processed.append(processed_post)

            except Exception as e:
                logger.warning(
                    f"Error processing post {post.get('post_id', 'unknown')}: {e}"
                )
                self.metrics.failed_chunks += 1

        return processed

    def process_chapters_data(self, chapters_dir: Optional[str] = None) -> bool:
        """Process chapter chunks with optimized pipeline."""
        chapters_dir = chapters_dir or (
            current_dir / "chapters" / "tools-in-data-science-public"
        )
        chapters_path = Path(chapters_dir)

        if not chapters_path.exists():
            logger.error(f"Chapters directory not found: {chapters_path}")
            return False

        logger.info(f"Processing chapters data from: {chapters_path}")

        # Define modules to process
        modules = [
            "development_tools",
            "deployment_tools",
            "large_language_models",
            "data_sourcing",
            "data_preparation",
            "data_analysis",
            "data_visualization",
            "project-1",
            "project-2",
            "misc",
        ]

        all_processed_chunks = []

        for module in modules:
            logger.info(f"Processing module: {module}")

            # Process module chunks
            chunks_file = chapters_path / module / "chunks.json"
            if not chunks_file.exists():
                logger.warning(f"No chunks.json found for module: {module}")
                continue

            with open(chunks_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            logger.info(f"Loaded {len(chunks)} chunks from {module}")

            # Process and validate chunks
            processed_chunks = []
            for chunk in chunks:
                if self.validate_chunk(chunk):
                    # Clean content
                    clean_content, metadata = self.clean_text_content(chunk["content"])

                    processed_chunk = {
                        "id": chunk["chunk_id"],
                        "content": chunk["content"],
                        "clean_content": clean_content,
                        "module": module,
                        "file_path": chunk.get("file_path", ""),
                        "chunk_index": chunk.get("chunk_index", 0),
                        "content_type": "markdown",
                        **metadata,
                    }
                    processed_chunks.append(processed_chunk)
                else:
                    self.metrics.failed_chunks += 1

            # Create module collection
            collection_name = f"chapters_{module}"
            self.create_or_update_collection(collection_name, "chapters")

            if processed_chunks:
                # Generate embeddings
                logger.info(
                    f"Generating embeddings for {len(processed_chunks)} chunks in {module}..."
                )
                start_time = time.time()

                texts = [chunk["clean_content"] for chunk in processed_chunks]
                embeddings = self.embedding_provider.generate_embeddings(
                    texts, batch_size=self.batch_size
                )

                self.metrics.embedding_time += time.time() - start_time

                # Prepare documents with embeddings
                documents = []
                for chunk, embedding in zip(processed_chunks, embeddings):
                    if embedding:
                        chunk["embedding"] = embedding
                        documents.append(chunk)
                    else:
                        self.metrics.failed_chunks += 1

                # Index to Typesense
                logger.info(f"Indexing {len(documents)} chunks to {collection_name}...")
                start_time = time.time()

                self._batch_index_documents(collection_name, documents)

                self.metrics.indexing_time += time.time() - start_time
                self.metrics.processed_chunks += len(documents)

                all_processed_chunks.extend(documents)

            self.metrics.total_chunks += len(chunks)

        # Save all processed chapter data
        output_file = self.output_dir / "processed_chapters.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_processed_chunks, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved processed chapter data to: {output_file}")
        return True

    def _batch_index_documents(
        self, collection_name: str, documents: List[Dict]
    ) -> None:
        """Index documents to Typesense in batches using proper JSONL format."""
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i : i + self.batch_size]

            # Convert to JSONL format (newline-delimited JSON)
            jsonl_lines = []
            for doc in batch:
                try:
                    jsonl_lines.append(json.dumps(doc, ensure_ascii=False))
                except Exception as e:
                    logger.warning(
                        f"Error serializing document {doc.get('id', 'unknown')}: {e}"
                    )

            if jsonl_lines:
                try:
                    # Create JSONL string - each JSON object on a separate line
                    jsonl_string = "\n".join(jsonl_lines)

                    # Import documents with proper JSONL format
                    response = self.client.collections[
                        collection_name
                    ].documents.import_(jsonl_string, {"action": "upsert"})

                    # Process response - Typesense returns one JSON response per line
                    success_count = 0
                    failed_count = 0

                    # Split response by lines and parse each line as JSON
                    response_lines = (
                        response.strip().split("\n") if response.strip() else []
                    )

                    for line in response_lines:
                        if line.strip():
                            try:
                                result = json.loads(line.strip())
                                if result.get("success", False):
                                    success_count += 1
                                else:
                                    failed_count += 1
                                    logger.warning(
                                        f"Failed to index document: {result.get('error', 'Unknown error')}"
                                    )
                            except json.JSONDecodeError as e:
                                logger.warning(
                                    f"Error parsing response line: {line} - {e}"
                                )
                                failed_count += 1

                    logger.info(
                        f"Batch {i//self.batch_size + 1}: Successfully indexed {success_count} documents, "
                        f"failed: {failed_count}, total batch size: {len(batch)}"
                    )

                except Exception as e:
                    logger.error(f"Batch indexing error for {collection_name}: {e}")
                    logger.error(
                        f"Batch documents: {[doc.get('id', 'unknown') for doc in batch]}"
                    )

    def create_unified_collection(self) -> bool:
        """Create a unified collection combining discourse and chapters data."""
        logger.info("Creating unified collection...")

        unified_collection = "unified_knowledge_base"
        self.create_or_update_collection(unified_collection, "chapters")

        # Load processed data
        discourse_file = self.output_dir / "processed_discourse_posts.json"
        chapters_file = self.output_dir / "processed_chapters.json"

        all_documents = []

        # Load discourse data
        if discourse_file.exists():
            with open(discourse_file, "r", encoding="utf-8") as f:
                discourse_data = json.load(f)

            for doc in discourse_data:
                doc["source_type"] = "discourse"
                doc["id"] = f"discourse_{doc['id']}"
                all_documents.append(doc)

        # Load chapters data
        if chapters_file.exists():
            with open(chapters_file, "r", encoding="utf-8") as f:
                chapters_data = json.load(f)

            for doc in chapters_data:
                doc["source_type"] = "chapters"
                doc["id"] = f"chapters_{doc['id']}"
                all_documents.append(doc)

        if all_documents:
            logger.info(
                f"Indexing {len(all_documents)} documents to unified collection..."
            )
            self._batch_index_documents(unified_collection, all_documents)

            # Save unified data
            output_file = self.output_dir / "unified_knowledge_base.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_documents, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved unified knowledge base to: {output_file}")

        return True

    def run_full_pipeline(self) -> None:
        """Run the complete optimized RAG pipeline."""
        logger.info("Starting optimized RAG pipeline...")
        logger.info("=" * 50)

        self.metrics = ProcessingMetrics()

        try:
            # Process discourse data
            logger.info("Step 1: Processing discourse data...")
            discourse_success = self.process_discourse_data()

            # Process chapters data
            logger.info("Step 2: Processing chapters data...")
            chapters_success = self.process_chapters_data()

            # Create unified collection
            if discourse_success or chapters_success:
                logger.info("Step 3: Creating unified collection...")
                self.create_unified_collection()

            self.metrics.end_time = datetime.now()

            # Print final metrics
            logger.info("Pipeline completed!")
            logger.info(self.metrics.summary())

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

    def test_search(
        self, query: str, collection_name: str = "unified_knowledge_base"
    ) -> List[Dict]:
        """Test search functionality using Typesense hybrid (keyword + vector) and multi-search APIs.
        See: https://typesense.org/docs/28.0/api/federated-multi-search.html#federated-search
        """
        try:
            logger.info(f"Searching in collection: {collection_name}")
            logger.info(f"Query: {query}")

            # Generate query embedding
            query_embedding = self.embedding_provider.generate_embeddings([query])[0]
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Format vector embedding as comma-separated string
            embedding_str = ",".join(map(str, query_embedding))

            # Hybrid search: combine keyword and vector search (see Typesense docs)
            search_parameters = {
                "collection": collection_name,
                "q": query,
                "query_by": "content",
                "vector_query": f"embedding:([{embedding_str}], alpha: 0.7)",
                "exclude_fields": "embedding",
                "limit": 10,
            }

            # Use MultiSearchRequestSchema: pass a dict with 'searches' key
            response = self.client.multi_search.perform(
                {"searches": [search_parameters]}
            )
            logger.info(f"Multi-search response: {response}")

            results = []
            # Parse response as per Typesense federated multi-search docs
            if response and isinstance(response, dict) and "results" in response:
                for search_result in response["results"]:
                    if "hits" in search_result:
                        for hit in search_result["hits"]:
                            doc = hit.get("document", {})
                            results.append(
                                {
                                    "id": doc.get("id"),
                                    "content": str(doc.get("content", ""))[:200]
                                    + "...",
                                    "score": hit.get("text_match", 0),
                                    "vector_distance": hit.get("vector_distance", 0),
                                    "source": doc.get("source_type", "unknown"),
                                    "module": doc.get("module", ""),
                                    "topic_title": doc.get("topic_title", ""),
                                }
                            )
            logger.info(f"Found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def test_hybrid_search(
        self,
        query: str,
        collection_name: str = "unified_knowledge_base",
        alpha: float = 0.7,
    ) -> List[Dict]:
        """Test hybrid search with customizable alpha parameter for vector/keyword weighting.

        Args:
            query: Search query
            collection_name: Typesense collection to search
            alpha: Weight for vector search (0.0 = pure keyword, 1.0 = pure vector)
        """
        try:
            logger.info(f"Hybrid search in collection: {collection_name}")
            logger.info(f"Query: {query}, Alpha: {alpha}")

            # Generate query embedding
            query_embedding = self.embedding_provider.generate_embeddings([query])[0]
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Format vector embedding for Typesense
            embedding_str = ",".join(map(str, query_embedding))

            # Hybrid search parameters based on official docs
            search_parameters = {
                "collection": collection_name,
                "q": query,
                "query_by": "content,clean_content",
                "vector_query": f"embedding:([{embedding_str}], alpha: {alpha})",
                "exclude_fields": "embedding",
                "per_page": 10,
                "drop_tokens_threshold": 0,  # For multi-word queries in hybrid search
                "rerank_hybrid_matches": True,  # Compute both scores for all matches
            }

            response = self.client.multi_search.perform(
                {"searches": [search_parameters]}
            )

            return self._parse_search_response(response, "hybrid")

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def test_semantic_search(
        self, query: str, collection_name: str = "unified_knowledge_base"
    ) -> List[Dict]:
        """Test pure semantic/vector search."""
        try:
            logger.info(f"Semantic search in collection: {collection_name}")
            logger.info(f"Query: {query}")

            # Generate query embedding
            query_embedding = self.embedding_provider.generate_embeddings([query])[0]
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Format vector embedding
            embedding_str = ",".join(map(str, query_embedding))

            # Pure semantic search (alpha = 1.0)
            search_parameters = {
                "collection": collection_name,
                "q": "*",  # Wildcard query for pure vector search
                "vector_query": f"embedding:([{embedding_str}], alpha: 1.0, k: 10)",
                "exclude_fields": "embedding",
                "per_page": 10,
            }

            response = self.client.multi_search.perform(
                {"searches": [search_parameters]}
            )

            return self._parse_search_response(response, "semantic")

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def test_federated_search(
        self, query: str, collections: List[str] = None
    ) -> Dict[str, List[Dict]]:
        """Test federated search across multiple collections."""
        try:
            if collections is None:
                collections = ["unified_knowledge_base", "discourse_posts_optimized"]

            logger.info(f"Federated search across collections: {collections}")
            logger.info(f"Query: {query}")

            # Generate query embedding once
            query_embedding = self.embedding_provider.generate_embeddings([query])[0]
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return {}

            embedding_str = ",".join(map(str, query_embedding))

            # Create search parameters for each collection
            searches = []
            for collection in collections:
                search_params = {
                    "collection": collection,
                    "q": query,
                    "query_by": "content,clean_content",
                    "vector_query": f"embedding:([{embedding_str}], alpha: 0.7)",
                    "exclude_fields": "embedding",
                    "per_page": 5,
                    "drop_tokens_threshold": 0,
                }
                searches.append(search_params)

            # Federated multi-search
            response = self.client.multi_search.perform({"searches": searches})

            # Parse results by collection
            results = {}
            if response and isinstance(response, dict) and "results" in response:
                for i, search_result in enumerate(response["results"]):
                    collection_name = (
                        collections[i] if i < len(collections) else f"collection_{i}"
                    )
                    results[collection_name] = self._parse_single_search_result(
                        search_result
                    )

            logger.info(f"Federated search completed across {len(results)} collections")
            return results

        except Exception as e:
            logger.error(f"Federated search failed: {e}")
            return {}

    def test_union_search(
        self, query: str, collections: List[str] = None
    ) -> List[Dict]:
        """Test union search that merges results from multiple collections."""
        try:
            if collections is None:
                collections = ["unified_knowledge_base"]

            logger.info(f"Union search across collections: {collections}")
            logger.info(f"Query: {query}")

            # Generate query embedding
            query_embedding = self.embedding_provider.generate_embeddings([query])[0]
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            embedding_str = ",".join(map(str, query_embedding))

            # Create search parameters for union search
            searches = []
            for collection in collections:
                search_params = {
                    "collection": collection,
                    "q": query,
                    "query_by": "content,clean_content",
                    "vector_query": f"embedding:([{embedding_str}], alpha: 0.7)",
                    "exclude_fields": "embedding",
                    "sort_by": "_text_match:desc",  # Same sorting for union
                }
                searches.append(search_params)

            # Union search with merged results
            response = self.client.multi_search.perform(
                {"union": True, "searches": searches}
            )

            return self._parse_search_response(response, "union")

        except Exception as e:
            logger.error(f"Union search failed: {e}")
            return []

    def test_similar_document_search(
        self, document_id: str, collection_name: str = "unified_knowledge_base"
    ) -> List[Dict]:
        """Test finding similar documents using document ID."""
        try:
            logger.info(f"Finding similar documents to ID: {document_id}")

            search_parameters = {
                "collection": collection_name,
                "q": "*",
                "vector_query": f"embedding:([], id: {document_id})",
                "exclude_fields": "embedding",
                "per_page": 10,
            }

            response = self.client.multi_search.perform(
                {"searches": [search_parameters]}
            )

            return self._parse_search_response(response, "similar")

        except Exception as e:
            logger.error(f"Similar document search failed: {e}")
            return []

    def test_advanced_hybrid_search(
        self,
        query: str,
        collection_name: str = "unified_knowledge_base",
        alpha: float = 0.7,
        distance_threshold: float = 0.5,
        filters: str = None,
        sort_by: str = "_text_match:desc",
    ) -> List[Dict]:
        """Test advanced hybrid search with filtering and distance threshold."""
        try:
            logger.info(f"Advanced hybrid search with filters: {filters}")
            logger.info(
                f"Query: {query}, Alpha: {alpha}, Distance threshold: {distance_threshold}"
            )

            # Generate query embedding
            query_embedding = self.embedding_provider.generate_embeddings([query])[0]
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            embedding_str = ",".join(map(str, query_embedding))

            # Advanced search parameters
            search_parameters = {
                "collection": collection_name,
                "q": query,
                "query_by": "content,clean_content",
                "vector_query": f"embedding:([{embedding_str}], alpha: {alpha}, distance_threshold: {distance_threshold})",
                "exclude_fields": "embedding",
                "per_page": 10,
                "sort_by": sort_by,
                "drop_tokens_threshold": 0,
                "rerank_hybrid_matches": True,
            }

            # Add filters if provided
            if filters:
                search_parameters["filter_by"] = filters

            response = self.client.multi_search.perform(
                {"searches": [search_parameters]}
            )

            return self._parse_search_response(response, "advanced_hybrid")

        except Exception as e:
            logger.error(f"Advanced hybrid search failed: {e}")
            return []

    def _parse_search_response(self, response, search_type: str) -> List[Dict]:
        """Parse Typesense search response."""
        results = []

        if not response or not isinstance(response, dict):
            return results

        # Handle union search response format
        if search_type == "union" and "hits" in response:
            for hit in response["hits"]:
                doc = hit.get("document", {})
                results.append(self._format_search_result(hit, doc))

        # Handle multi-search response format
        elif "results" in response:
            for search_result in response["results"]:
                if "hits" in search_result:
                    for hit in search_result["hits"]:
                        doc = hit.get("document", {})
                        results.append(self._format_search_result(hit, doc))

        logger.info(f"{search_type.title()} search found {len(results)} results")
        return results

    def _parse_single_search_result(self, search_result: Dict) -> List[Dict]:
        """Parse a single search result from multi-search response."""
        results = []
        if "hits" in search_result:
            for hit in search_result["hits"]:
                doc = hit.get("document", {})
                results.append(self._format_search_result(hit, doc))
        return results

    def _format_search_result(self, hit: Dict, doc: Dict) -> Dict:
        """Format a search result for consistent output."""
        return {
            "id": doc.get("id"),
            "content": str(doc.get("content", ""))[:200] + "...",
            "clean_content": str(doc.get("clean_content", ""))[:200] + "...",
            "text_match_score": hit.get("text_match", 0),
            "vector_distance": hit.get("vector_distance", None),
            "source": doc.get("source_type", "unknown"),
            "module": doc.get("module", ""),
            "topic_title": doc.get("topic_title", ""),
            "username": doc.get("username", ""),
            "has_code": doc.get("has_code", False),
            "content_length": doc.get("content_length", 0),
        }

    def comprehensive_search_test(self, query: str) -> Dict:
        """Run comprehensive search tests across all methods."""
        logger.info(f"=== Comprehensive Search Test for: '{query}' ===")

        results = {"query": query, "timestamp": datetime.now().isoformat(), "tests": {}}

        # Test 1: Basic hybrid search
        logger.info("1. Testing basic hybrid search...")
        results["tests"]["hybrid_search"] = self.test_hybrid_search(query)

        # Test 2: Semantic search
        logger.info("2. Testing semantic search...")
        results["tests"]["semantic_search"] = self.test_semantic_search(query)

        # Test 3: Federated search
        logger.info("3. Testing federated search...")
        results["tests"]["federated_search"] = self.test_federated_search(query)

        # Test 4: Advanced hybrid with filters
        logger.info("4. Testing advanced hybrid search...")
        results["tests"]["advanced_hybrid"] = self.test_advanced_hybrid_search(
            query, alpha=0.8, distance_threshold=0.6, filters="has_code:true"
        )

        # Test 5: Different alpha values
        alphas = [0.3, 0.5, 0.7, 0.9]
        results["tests"]["alpha_comparison"] = {}
        for alpha in alphas:
            logger.info(f"5. Testing alpha={alpha}...")
            results["tests"]["alpha_comparison"][f"alpha_{alpha}"] = (
                self.test_hybrid_search(query, alpha=alpha)
            )

        logger.info("=== Comprehensive Search Test Completed ===")
        return results


def main():
    """Main function to run the optimized RAG pipeline."""
    pipeline = OptimizedRAGPipeline()

    # Run full pipeline
    pipeline.run_full_pipeline()

    # Test search functionality
    logger.info("\nTesting comprehensive search functionality...")
    test_queries = [
        "data visualization techniques",
        "machine learning models",
        "project deployment",
        "data preparation",
    ]

    for query in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing query: '{query}'")
        logger.info(f"{'='*60}")

        # Run comprehensive search test
        comprehensive_results = pipeline.comprehensive_search_test(query)

        # Save results to file
        output_file = (
            pipeline.output_dir / f"search_test_{query.replace(' ', '_')}.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)

        logger.info(f"Comprehensive search results saved to: {output_file}")


if __name__ == "__main__":
    main()
