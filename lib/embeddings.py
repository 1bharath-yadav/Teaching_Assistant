"""
Unified Embedding System for Teaching Assistant

This module provides a unified interface for generating embeddings using different providers:
- OpenAI (remote API)
- Ollama (local LLM server)
- Azure OpenAI (remote API)

Usage:
    from lib.embeddings import generate_embedding, batch_generate_embeddings

    # Single embedding
    embedding = generate_embedding("Hello world")

    # Batch embeddings
    embeddings = batch_generate_embeddings(["Hello", "World", "Test"])
"""

import logging
from typing import List, Optional, Dict, Any
from .config import get_config, get_embedding_config
import time
import requests

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Base class for embedding providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def generate_single(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        raise NotImplementedError

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        # Default implementation: generate one by one
        embeddings = []
        for text in texts:
            embedding = self.generate_single(text)
            embeddings.append(embedding)
        return embeddings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using OpenAI API"""

    def __init__(self, config: Dict[str, Any], api_config: Dict[str, Any]):
        super().__init__(config)
        self.api_config = api_config
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(
                base_url=self.api_config.get("base_url", "https://api.openai.com/v1"),
                api_key=self.api_config.get("api_key", ""),
            )
        return self._client

    def generate_single(self, text: str) -> List[float]:
        """Generate embedding for a single text using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model=self.config.get("model", "text-embedding-3-small"), input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            return [0.0] * self.config.get("dimensions", 1536)

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI batch API"""
        try:
            response = self.client.embeddings.create(
                model=self.config.get("model", "text-embedding-3-small"), input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error generating OpenAI batch embeddings: {e}")
            # Fallback to individual generation
            return super().generate_batch(texts)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider using Ollama's local server"""

    def __init__(self, config: Dict[str, Any], api_config: Dict[str, Any]):
        super().__init__(config)
        self.api_config = api_config
        self.base_url = (
            api_config.get("base_url", "http://localhost:11434")
            .rstrip("/v1")
            .rstrip("/")
        )

    def generate_single(self, text: str) -> List[float]:
        """Generate embedding for a single text using Ollama API"""
        try:
            url = f"{self.base_url}/api/embeddings"
            data = {
                "model": self.config.get("model", "nomic-embed-text"),
                "prompt": text,
            }

            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            if "embedding" in result:
                return result["embedding"]
            else:
                logger.error(f"Unexpected Ollama response format: {result}")
                return [0.0] * self.config.get("dimensions", 768)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Ollama: {e}")
            return [0.0] * self.config.get("dimensions", 768)
        except Exception as e:
            logger.error(f"Error generating Ollama embedding: {e}")
            return [0.0] * self.config.get("dimensions", 768)

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Ollama"""
        embeddings = []
        total = len(texts)

        for i, text in enumerate(texts, 1):
            if i % 10 == 0 or i == total:
                logger.info(f"Generating Ollama embedding {i}/{total}...")

            embedding = self.generate_single(text)
            embeddings.append(embedding)

            # Small delay to avoid overwhelming the local server
            if i < total:
                time.sleep(0.1)

        return embeddings


class AzureEmbeddingProvider(EmbeddingProvider):
    """Azure OpenAI embedding provider"""

    def __init__(self, config: Dict[str, Any], api_config: Dict[str, Any]):
        super().__init__(config)
        self.api_config = api_config
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Azure OpenAI client"""
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(
                base_url=self.api_config.get("base_url", ""),
                api_key=self.api_config.get("api_key", ""),
            )
        return self._client

    def generate_single(self, text: str) -> List[float]:
        """Generate embedding for a single text using Azure OpenAI"""
        try:
            response = self.client.embeddings.create(
                model=self.config.get("model", "text-embedding-ada-002"), input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating Azure embedding: {e}")
            return [0.0] * self.config.get("dimensions", 1536)


def _get_embedding_provider() -> EmbeddingProvider:
    """Get the configured embedding provider"""
    app_config = get_config()
    embedding_config = get_embedding_config()
    provider_name = app_config.defaults.embedding_provider

    if provider_name == "openai":
        return OpenAIEmbeddingProvider(
            config=embedding_config,
            api_config={
                "base_url": app_config.openai.base_url,
                "api_key": app_config.openai.api_key,
            },
        )
    elif provider_name == "ollama":
        return OllamaEmbeddingProvider(
            config=embedding_config,
            api_config={
                "base_url": app_config.ollama.base_url,
                "api_key": app_config.ollama.api_key,
            },
        )
    elif provider_name == "azure":
        return AzureEmbeddingProvider(
            config=embedding_config,
            api_config={
                "base_url": app_config.azure.base_url,
                "api_key": app_config.azure.api_key,
            },
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider_name}")


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text using the configured provider.

    Args:
        text: Text to generate embedding for

    Returns:
        List of floats representing the embedding
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        app_config = get_config()
        embedding_config = get_embedding_config()
        return [0.0] * embedding_config.get("dimensions", 1536)

    provider = _get_embedding_provider()
    return provider.generate_single(text.strip())


def batch_generate_embeddings(
    texts: List[str], batch_size: Optional[int] = None
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts using the configured provider.

    Args:
        texts: List of texts to generate embeddings for
        batch_size: Optional batch size for processing (provider-dependent)

    Returns:
        List of embeddings (each embedding is a list of floats)
    """
    if not texts:
        logger.warning("Empty text list provided for batch embedding")
        return []

    # Filter out empty texts
    processed_texts = []
    indices = []
    for i, text in enumerate(texts):
        if text and text.strip():
            processed_texts.append(text.strip())
            indices.append(i)

    if not processed_texts:
        logger.warning("All texts were empty after filtering")
        app_config = get_config()
        embedding_config = get_embedding_config()
        dimensions = embedding_config.get("dimensions", 1536)
        return [[0.0] * dimensions for _ in texts]

    provider = _get_embedding_provider()

    # Generate embeddings for non-empty texts
    if batch_size and len(processed_texts) > batch_size:
        # Process in batches
        all_embeddings = []
        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i : i + batch_size]
            batch_embeddings = provider.generate_batch(batch)
            all_embeddings.extend(batch_embeddings)

            logger.info(
                f"Processed batch {i//batch_size + 1}/{(len(processed_texts) + batch_size - 1)//batch_size}"
            )
    else:
        # Process all at once
        all_embeddings = provider.generate_batch(processed_texts)

    # Reconstruct full results with empty embeddings for filtered texts
    app_config = get_config()
    embedding_config = get_embedding_config()
    dimensions = embedding_config.get("dimensions", 1536)

    result = []
    embedding_idx = 0

    for i, text in enumerate(texts):
        if i in indices:
            if embedding_idx < len(all_embeddings):
                result.append(all_embeddings[embedding_idx])
                embedding_idx += 1
            else:
                result.append([0.0] * dimensions)
        else:
            result.append([0.0] * dimensions)

    return result


def get_embedding_dimensions() -> int:
    """Get the dimensions of embeddings from the current provider"""
    embedding_config = get_embedding_config()
    return embedding_config.get("dimensions", 1536)


def test_embedding_provider():
    """Test the current embedding provider with a simple text"""
    try:
        test_text = "This is a test sentence for embedding generation."
        embedding = generate_embedding(test_text)

        app_config = get_config()
        provider_name = app_config.defaults.embedding_provider

        print(f"Testing {provider_name} embedding provider...")
        print(f"Text: {test_text}")
        print(f"Embedding dimensions: {len(embedding)}")
        print(f"Sample values: {embedding[:5] if len(embedding) >= 5 else embedding}")

        # Test batch generation
        batch_texts = ["Hello world", "Test embedding", "Another sentence"]
        batch_embeddings = batch_generate_embeddings(batch_texts)
        print(f"Batch test: Generated {len(batch_embeddings)} embeddings")

        return True

    except Exception as e:
        print(f"Error testing embedding provider: {e}")
        return False


if __name__ == "__main__":
    # Test the embedding system
    test_embedding_provider()
