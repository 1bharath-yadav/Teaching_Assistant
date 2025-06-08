#!/usr/bin/env python3
"""
Enhanced Configuration Management for RAG Pipeline

This script provides improved configuration validation and management
specifically for the RAG pipeline operations.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Embedding configuration."""

    provider: str
    model: str
    dimensions: int
    batch_size: int = 100
    max_retries: int = 3
    timeout: int = 30


@dataclass
class TypesenseConfig:
    """Typesense configuration."""

    host: str
    port: int
    protocol: str
    api_key: str
    connection_timeout: int = 10


@dataclass
class ProcessingConfig:
    """Data processing configuration."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_length: int = 50
    max_chunk_length: int = 8000
    batch_size: int = 100
    enable_html_cleaning: bool = True
    enable_content_validation: bool = True


class EnhancedConfigManager:
    """Enhanced configuration manager for RAG pipeline."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        if config_path is None:
            # Try to find config.yaml in project root
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            config_path = project_root / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)

        # Expand environment variables
        config = self._expand_env_vars(config)

        return config

    def _expand_env_vars(self, obj):
        """Recursively expand environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Handle ${VAR:-default} syntax
            if obj.startswith("${") and obj.endswith("}"):
                var_expr = obj[2:-1]
                if ":-" in var_expr:
                    var_name, default_value = var_expr.split(":-", 1)
                    return os.getenv(var_name, default_value)
                else:
                    return os.getenv(var_expr, obj)
            return obj
        else:
            return obj

    def _validate_config(self):
        """Validate configuration values."""
        required_sections = ["embeddings", "typesense"]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate embedding configuration
        embedding_config = self.config["embeddings"]
        if "provider" not in embedding_config:
            raise ValueError("Missing embeddings.provider in configuration")

        provider = embedding_config["provider"]
        if provider not in embedding_config:
            raise ValueError(
                f"Missing configuration for embedding provider: {provider}"
            )

        # Validate Typesense configuration
        typesense_config = self.config["typesense"]
        required_typesense_fields = ["api_key", "nodes"]
        for field in required_typesense_fields:
            if field not in typesense_config:
                raise ValueError(f"Missing typesense.{field} in configuration")

    def get_embedding_config(self) -> EmbeddingConfig:
        """Get embedding configuration."""
        embedding_config = self.config["embeddings"]
        provider = embedding_config["provider"]
        provider_config = embedding_config[provider]

        return EmbeddingConfig(
            provider=provider,
            model=provider_config["model"],
            dimensions=provider_config["dimensions"],
            batch_size=embedding_config.get("batch_size", 100),
            max_retries=embedding_config.get("max_retries", 3),
            timeout=embedding_config.get("timeout", 30),
        )

    def get_typesense_config(self) -> TypesenseConfig:
        """Get Typesense configuration."""
        typesense_config = self.config["typesense"]
        node = typesense_config["nodes"][0]  # Use first node

        return TypesenseConfig(
            host=node["host"],
            port=int(node["port"]),
            protocol=node["protocol"],
            api_key=typesense_config["api_key"],
            connection_timeout=typesense_config.get("connection_timeout", 10),
        )

    def get_processing_config(self) -> ProcessingConfig:
        """Get processing configuration."""
        # Get from document_processing section or use defaults
        doc_config = self.config.get("document_processing", {})
        discourse_config = self.config.get("discourse", {})

        return ProcessingConfig(
            chunk_size=doc_config.get("chunk_size", 1000),
            chunk_overlap=doc_config.get("chunk_overlap", 200),
            min_chunk_length=doc_config.get("min_chunk_length", 50),
            max_chunk_length=doc_config.get("max_chunk_length", 8000),
            batch_size=discourse_config.get("batch_size", 100),
            enable_html_cleaning=discourse_config.get("enable_html_cleaning", True),
            enable_content_validation=doc_config.get("enable_content_validation", True),
        )

    def get_api_config(self, provider: str) -> Dict[str, Any]:
        """Get API configuration for a specific provider."""
        provider_configs = {
            "openai": self.config.get("openai", {}),
            "ollama": self.config.get("ollama", {}),
            "azure": self.config.get("azure", {}),
        }

        if provider not in provider_configs:
            raise ValueError(f"Unknown provider: {provider}")

        config = provider_configs[provider]

        # Ensure required fields are present
        if provider == "openai":
            required_fields = ["api_key", "base_url"]
        elif provider == "ollama":
            required_fields = ["base_url"]
        elif provider == "azure":
            required_fields = ["api_key", "base_url", "api_version"]

        for field in required_fields:
            if field not in config:
                logger.warning(f"Missing {field} for {provider} provider")

        return config

    def get_collection_config(self, collection_type: str) -> Dict[str, Any]:
        """Get collection-specific configuration."""
        collections_config = self.config.get("typesense", {}).get("collections", {})
        return collections_config.get(collection_type, {})

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration values."""

        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        self.config = deep_update(self.config, updates)

    def save_config(self, output_path: Optional[str] = None):
        """Save configuration to file."""
        output_path = output_path or self.config_path

        with open(output_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)

        logger.info(f"Configuration saved to: {output_path}")

    def validate_embedding_provider(self, provider: str) -> bool:
        """Validate that embedding provider is properly configured."""
        try:
            config = self.get_api_config(provider)
            embedding_config = self.get_embedding_config()

            if embedding_config.provider != provider:
                return False

            # Provider-specific validation
            if provider == "openai":
                return bool(config.get("api_key")) and bool(config.get("base_url"))
            elif provider == "ollama":
                return bool(config.get("base_url"))
            elif provider == "azure":
                required = ["api_key", "base_url", "api_version"]
                return all(config.get(field) for field in required)

            return True

        except Exception as e:
            logger.error(f"Error validating {provider} provider: {e}")
            return False

    def get_optimal_batch_size(self, provider: str) -> int:
        """Get optimal batch size for embedding provider."""
        # Provider-specific optimal batch sizes
        optimal_sizes = {
            "openai": 100,  # OpenAI can handle larger batches
            "ollama": 50,  # Local models may be more limited
            "azure": 100,  # Similar to OpenAI
        }

        base_size = optimal_sizes.get(provider, 50)

        # Adjust based on configuration
        config_batch_size = self.get_processing_config().batch_size

        # Use the smaller of configured or optimal
        return min(base_size, config_batch_size)

    def get_collection_settings(self) -> Dict[str, Any]:
        """Get optimized collection settings."""
        return {
            "enable_nested_fields": True,
            "token_separators": ["-", "_", ".", " "],
            "symbols_to_index": ["#", "@"],
            "default_sorting_field": "content_length",
        }


def get_enhanced_config(config_path: Optional[str] = None) -> EnhancedConfigManager:
    """Get enhanced configuration manager instance."""
    return EnhancedConfigManager(config_path)


# Example usage and validation
if __name__ == "__main__":
    try:
        config_manager = get_enhanced_config()

        print("Configuration loaded successfully!")
        print(f"Embedding provider: {config_manager.get_embedding_config().provider}")
        print(f"Embedding model: {config_manager.get_embedding_config().model}")
        print(
            f"Embedding dimensions: {config_manager.get_embedding_config().dimensions}"
        )

        typesense_config = config_manager.get_typesense_config()
        print(
            f"Typesense: {typesense_config.protocol}://{typesense_config.host}:{typesense_config.port}"
        )

        processing_config = config_manager.get_processing_config()
        print(f"Batch size: {processing_config.batch_size}")
        print(f"Chunk size: {processing_config.chunk_size}")

    except Exception as e:
        print(f"Configuration error: {e}")
