"""
Centralized Configuration System for Teaching Assistant

This module provides a unified configuration interface that loads settings from:
1. config.yaml (main configuration file)
2. Environment variables (with override capability)
3. .env file (fallback for sensitive values)

Usage:
    from lib.config import get_config, get_openai_client, get_typesense_client

    config = get_config()
    print(config.openai.api_key)
    print(config.ollama.models)

    # Get pre-configured clients
    openai_client = get_openai_client()
    typesense_client = get_typesense_client()
"""

import os
import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    organization_id: str = ""
    models: List[str] = field(default_factory=list)
    default_model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class OllamaConfig:
    """Ollama local LLM configuration"""

    base_url: str = "http://localhost:11434/v1"
    api_key: str = "not-needed"
    models: List[str] = field(default_factory=list)
    default_model: str = "llama3.2:3b"
    max_tokens: int = 4096
    temperature: float = 0.7
    embedding_models: List[str] = field(default_factory=list)


@dataclass
class AzureConfig:
    """Azure OpenAI configuration"""

    enabled: bool = False
    api_key: str = ""
    base_url: str = ""
    api_version: str = "2023-12-01-preview"
    deployment_name: str = ""


@dataclass
class AnthropicConfig:
    """Anthropic Claude configuration"""

    enabled: bool = False
    api_key: str = ""
    base_url: str = "https://api.anthropic.com"
    api_version: str = "2023-06-01"
    models: List[str] = field(default_factory=list)


@dataclass
class GoogleConfig:
    """Google Gemini configuration"""

    enabled: bool = False
    api_key: str = ""
    base_url: str = "https://generativelanguage.googleapis.com"
    models: List[str] = field(default_factory=list)


@dataclass
class TypesenseNode:
    """Typesense node configuration"""

    host: str = "localhost"
    port: str = "8108"
    protocol: str = "http"


@dataclass
class TypesenseConfig:
    """Typesense search engine configuration"""

    api_key: str = ""
    nodes: List[TypesenseNode] = field(default_factory=list)
    connection_timeout: int = 10
    collections: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class EmbeddingProviderConfig:
    """Individual embedding provider configuration"""

    model: str = ""
    dimensions: int = 768


@dataclass
class EmbeddingsConfig:
    """Embeddings configuration"""

    provider: str = "ollama"
    openai: EmbeddingProviderConfig = field(default_factory=EmbeddingProviderConfig)
    ollama: EmbeddingProviderConfig = field(default_factory=EmbeddingProviderConfig)
    azure: EmbeddingProviderConfig = field(default_factory=EmbeddingProviderConfig)


@dataclass
class AppConfig:
    """Application settings"""

    name: str = "Teaching Assistant"
    version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"


@dataclass
class FrontendConfig:
    """Frontend configuration"""

    port: int = 3000
    host: str = "localhost"
    api_base_path: str = "/api"


@dataclass
class APIConfig:
    """Backend API configuration"""

    port: int = 8000
    host: str = "localhost"
    workers: int = 1
    cors_origins: List[str] = field(default_factory=list)


@dataclass
class SecurityConfig:
    """Security configuration"""

    access_codes: List[str] = field(default_factory=list)
    enable_api_key_auth: bool = False
    allowed_origins: List[str] = field(default_factory=list)


@dataclass
class DocumentProcessingConfig:
    """Document processing configuration"""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    supported_formats: List[str] = field(default_factory=list)


@dataclass
class DiscourseConfig:
    """Discourse processing configuration"""

    input_file: str = "data/discourse/scraped_posts.json"
    output_file: str = "data/discourse/processed_posts.json"
    batch_size: int = 100
    enable_html_cleaning: bool = True
    enable_embeddings: bool = True


@dataclass
class ChunkingConfig:
    """Chunking configuration for chapters"""

    intelligent_splitting: bool = True
    preserve_headers: bool = True
    extract_metadata: bool = True


@dataclass
class ChaptersConfig:
    """Chapters processing configuration"""

    repository_url: str = "https://github.com/sanand0/tools-in-data-science-public.git"
    local_path: str = "data/chapters/tools-in-data-science-public"
    modules: List[str] = field(default_factory=list)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)


@dataclass
class RagPipelineConfig:
    """RAG Pipeline configuration"""

    enable_batch_processing: bool = True
    max_concurrent_requests: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_progress_tracking: bool = True
    save_intermediate_results: bool = True


@dataclass
class QualityControlConfig:
    """Quality control configuration"""

    min_content_length: int = 50
    max_content_length: int = 8000
    min_alpha_ratio: float = 0.3
    skip_header_only_chunks: bool = True
    validate_embeddings: bool = True


@dataclass
class DefaultsConfig:
    """Default provider selection"""

    chat_provider: str = "ollama"
    embedding_provider: str = "ollama"
    search_provider: str = "typesense"
    tool_calling_model: str = "llama3.2:1b"


@dataclass
class HybridSearchPromptsConfig:
    """Prompts configuration for hybrid search"""

    classification_system: str = (
        "Your task is to classify the user's question into one or more relevant collections of the Data Science course."
    )
    assistant_system: str = """You are a helpful teaching assistant for a Tools in datascience(TDS) course in IIT Madras. Your task is to answer student questions using the provided course content.

Guidelines:
1. Provide clear, accurate, and helpful answers based on the course content
2. If the content doesn't fully answer the question, say so and provide what information is available
3. Use examples from the course content when relevant
4. Be encouraging and supportive in your tone
5. provide relevant links or resources in the content.
6. Structure your answer in a logical, easy-to-follow manner"""
    link_extraction_system: str = (
        "Extract any URLs and links from the given content. Return as JSON array."
    )


@dataclass
class HybridSearchAnswerGenerationConfig:
    """Answer generation settings for hybrid search"""

    enable_streaming: bool = True
    enable_link_extraction: bool = True
    max_sources: int = 10
    deduplicate_content: bool = True
    include_source_info: bool = True


@dataclass
class HybridSearchFallbackConfig:
    """Fallback settings for hybrid search"""

    enable_keyword_search: bool = True
    min_results_threshold: int = 1
    error_messages: Dict[str, str] = field(
        default_factory=lambda: {
            "no_results": "I couldn't find relevant information for your question. Please try rephrasing or asking a more specific question.",
            "search_error": "I encountered an error while processing your question. Please try again.",
            "generation_error": "I found relevant information but encountered an issue generating the response. Please try again.",
        }
    )


@dataclass
class HybridSearchConfig:
    """Hybrid search configuration"""

    alpha: float = 0.7
    top_k: int = 10
    max_context_length: int = 50000
    num_typos: int = 2
    default_collections: List[str] = field(default_factory=list)
    available_collections: List[str] = field(default_factory=list)
    answer_generation: HybridSearchAnswerGenerationConfig = field(
        default_factory=HybridSearchAnswerGenerationConfig
    )
    prompts: HybridSearchPromptsConfig = field(
        default_factory=HybridSearchPromptsConfig
    )
    fallback: HybridSearchFallbackConfig = field(
        default_factory=HybridSearchFallbackConfig
    )


@dataclass
class TeachingAssistantConfig:
    """Main configuration class"""

    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    azure: AzureConfig = field(default_factory=AzureConfig)
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    google: GoogleConfig = field(default_factory=GoogleConfig)
    typesense: TypesenseConfig = field(default_factory=TypesenseConfig)
    embeddings: EmbeddingsConfig = field(default_factory=EmbeddingsConfig)
    app: AppConfig = field(default_factory=AppConfig)
    frontend: FrontendConfig = field(default_factory=FrontendConfig)
    api: APIConfig = field(default_factory=APIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    document_processing: DocumentProcessingConfig = field(
        default_factory=DocumentProcessingConfig
    )
    discourse: DiscourseConfig = field(default_factory=DiscourseConfig)
    chapters: ChaptersConfig = field(default_factory=ChaptersConfig)
    rag_pipeline: RagPipelineConfig = field(default_factory=RagPipelineConfig)
    quality_control: QualityControlConfig = field(default_factory=QualityControlConfig)
    hybrid_search: HybridSearchConfig = field(default_factory=HybridSearchConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    model_dimensions: Dict[str, int] = field(default_factory=dict)


class ConfigLoader:
    """Configuration loader with environment variable override support"""

    def __init__(self, config_path: str = "config.yaml"):
        # If config_path is relative, make it relative to the project root
        if not Path(config_path).is_absolute():
            # Find the project root by looking for config.yaml or pyproject.toml
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent  # lib -> project_root
            self.config_path = project_root / config_path
        else:
            self.config_path = Path(config_path)
        self._config: Optional[TeachingAssistantConfig] = None

    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in configuration values"""
        if isinstance(obj, str):
            # Handle ${VAR:-default} syntax
            if obj.startswith("${") and obj.endswith("}"):
                var_expr = obj[2:-1]  # Remove ${ and }
                if ":-" in var_expr:
                    var_name, default_value = var_expr.split(":-", 1)
                    return os.getenv(var_name, default_value)
                else:
                    return os.getenv(var_expr, obj)
            return obj
        elif isinstance(obj, dict):
            return {key: self._expand_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        else:
            return obj

    def _dict_to_dataclass(self, data_dict: Dict[str, Any], dataclass_type) -> Any:
        """Convert dictionary to dataclass instance"""
        if not data_dict:
            return dataclass_type()

        # Get field types from dataclass
        field_types = {
            f.name: f.type for f in dataclass_type.__dataclass_fields__.values()
        }
        kwargs = {}

        for key, value in data_dict.items():
            if key in field_types:
                field_type = field_types[key]

                # Handle nested dataclasses
                if hasattr(field_type, "__dataclass_fields__"):
                    kwargs[key] = self._dict_to_dataclass(value, field_type)
                # Handle List[dataclass] types
                elif (
                    hasattr(field_type, "__origin__") and field_type.__origin__ is list
                ):
                    if hasattr(field_type.__args__[0], "__dataclass_fields__"):
                        kwargs[key] = [
                            self._dict_to_dataclass(item, field_type.__args__[0])
                            for item in value
                        ]
                    else:
                        kwargs[key] = value
                else:
                    kwargs[key] = value

        return dataclass_type(**kwargs)

    def load_config(self) -> TeachingAssistantConfig:
        """Load configuration from YAML file with environment variable expansion"""
        if not self.config_path.exists():
            logger.warning(
                f"Configuration file {self.config_path} not found. Using defaults."
            )
            return TeachingAssistantConfig()

        try:
            with open(self.config_path, "r") as f:
                raw_config = yaml.safe_load(f)

            # Expand environment variables
            expanded_config = self._expand_env_vars(raw_config)

            # Convert to dataclass
            config = TeachingAssistantConfig()

            # Map configuration sections to dataclass fields
            if "openai" in expanded_config:
                config.openai = self._dict_to_dataclass(
                    expanded_config["openai"], OpenAIConfig
                )

            if "ollama" in expanded_config:
                config.ollama = self._dict_to_dataclass(
                    expanded_config["ollama"], OllamaConfig
                )

            if "azure" in expanded_config:
                config.azure = self._dict_to_dataclass(
                    expanded_config["azure"], AzureConfig
                )

            if "anthropic" in expanded_config:
                config.anthropic = self._dict_to_dataclass(
                    expanded_config["anthropic"], AnthropicConfig
                )

            if "google" in expanded_config:
                config.google = self._dict_to_dataclass(
                    expanded_config["google"], GoogleConfig
                )

            if "typesense" in expanded_config:
                # Handle TypesenseConfig specially due to nodes list
                ts_config = expanded_config["typesense"]
                nodes = []
                if "nodes" in ts_config:
                    for node_data in ts_config["nodes"]:
                        nodes.append(TypesenseNode(**node_data))

                config.typesense = TypesenseConfig(
                    api_key=ts_config.get("api_key", ""),
                    nodes=nodes,
                    connection_timeout=ts_config.get("connection_timeout", 10),
                    collections=ts_config.get("collections", {}),
                )

            if "embeddings" in expanded_config:
                emb_config = expanded_config["embeddings"]
                config.embeddings = EmbeddingsConfig(
                    provider=emb_config.get("provider", "ollama"),
                    openai=self._dict_to_dataclass(
                        emb_config.get("openai", {}), EmbeddingProviderConfig
                    ),
                    ollama=self._dict_to_dataclass(
                        emb_config.get("ollama", {}), EmbeddingProviderConfig
                    ),
                    azure=self._dict_to_dataclass(
                        emb_config.get("azure", {}), EmbeddingProviderConfig
                    ),
                )

            if "app" in expanded_config:
                config.app = self._dict_to_dataclass(expanded_config["app"], AppConfig)

            if "frontend" in expanded_config:
                config.frontend = self._dict_to_dataclass(
                    expanded_config["frontend"], FrontendConfig
                )

            if "api" in expanded_config:
                config.api = self._dict_to_dataclass(expanded_config["api"], APIConfig)

            if "security" in expanded_config:
                config.security = self._dict_to_dataclass(
                    expanded_config["security"], SecurityConfig
                )

            if "document_processing" in expanded_config:
                config.document_processing = self._dict_to_dataclass(
                    expanded_config["document_processing"], DocumentProcessingConfig
                )

            if "discourse" in expanded_config:
                config.discourse = self._dict_to_dataclass(
                    expanded_config["discourse"], DiscourseConfig
                )

            if "defaults" in expanded_config:
                config.defaults = self._dict_to_dataclass(
                    expanded_config["defaults"], DefaultsConfig
                )

            if "hybrid_search" in expanded_config:
                config.hybrid_search = self._dict_to_dataclass(
                    expanded_config["hybrid_search"], HybridSearchConfig
                )

            if "model_dimensions" in expanded_config:
                config.model_dimensions = expanded_config["model_dimensions"]

            return config

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return TeachingAssistantConfig()


# Global configuration instance
_config_loader = ConfigLoader()
_config_instance: Optional[TeachingAssistantConfig] = None


def get_config() -> TeachingAssistantConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = _config_loader.load_config()
    return _config_instance


def reload_config() -> TeachingAssistantConfig:
    """Reload configuration from file"""
    global _config_instance
    _config_instance = _config_loader.load_config()
    return _config_instance


# Convenience functions for getting pre-configured clients
def get_openai_client():
    """Get OpenAI client configured from centralized config"""
    from openai import OpenAI

    config = get_config()

    # Determine which provider to use based on defaults
    if config.defaults.chat_provider == "ollama":
        return OpenAI(
            base_url=config.ollama.base_url,
            api_key=config.ollama.api_key,
        )
    elif config.defaults.chat_provider == "azure" and config.azure.enabled:
        return OpenAI(
            base_url=config.azure.base_url,
            api_key=config.azure.api_key,
        )
    else:
        # Default to OpenAI
        return OpenAI(
            base_url=config.openai.base_url,
            api_key=config.openai.api_key,
        )


def get_typesense_client():
    """Get Typesense client configured from centralized config"""
    import typesense

    config = get_config()

    # Convert TypesenseNode dataclasses to dictionaries
    nodes = []
    for node in config.typesense.nodes:
        nodes.append({"host": node.host, "port": node.port, "protocol": node.protocol})

    return typesense.Client(
        {
            "api_key": config.typesense.api_key,
            "nodes": nodes,
            "connection_timeout_seconds": config.typesense.connection_timeout,
        }
    )


def get_embedding_client():
    """Get embedding client based on configured provider"""
    config = get_config()

    if config.defaults.embedding_provider == "openai":
        from openai import OpenAI

        return OpenAI(
            base_url=config.openai.base_url,
            api_key=config.openai.api_key,
        )
    elif config.defaults.embedding_provider == "ollama":
        from openai import OpenAI

        return OpenAI(
            base_url=config.ollama.base_url,
            api_key=config.ollama.api_key,
        )
    elif config.defaults.embedding_provider == "azure" and config.azure.enabled:
        from openai import OpenAI

        return OpenAI(
            base_url=config.azure.base_url,
            api_key=config.azure.api_key,
        )
    else:
        raise ValueError(
            f"Unsupported embedding provider: {config.defaults.embedding_provider}"
        )


def get_model_config(provider: str = None) -> Dict[str, Any]:
    """Get model configuration for a specific provider"""
    config = get_config()
    provider = provider or config.defaults.chat_provider

    if provider == "openai":
        return {
            "model": config.openai.default_model,
            "max_tokens": config.openai.max_tokens,
            "temperature": config.openai.temperature,
            "available_models": config.openai.models,
        }
    elif provider == "ollama":
        return {
            "model": config.ollama.default_model,
            "max_tokens": config.ollama.max_tokens,
            "temperature": config.ollama.temperature,
            "available_models": config.ollama.models,
        }
    elif provider == "azure":
        return {
            "deployment_name": config.azure.deployment_name,
            "api_version": config.azure.api_version,
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def get_embedding_config(provider: str = None) -> Dict[str, Any]:
    """Get embedding configuration for a specific provider"""
    config = get_config()
    provider = provider or config.defaults.embedding_provider

    if provider == "openai":
        return {
            "model": config.embeddings.openai.model,
            "dimensions": config.embeddings.openai.dimensions,
        }
    elif provider == "ollama":
        return {
            "model": config.embeddings.ollama.model,
            "dimensions": config.embeddings.ollama.dimensions,
            "available_models": config.ollama.embedding_models,
        }
    elif provider == "azure":
        return {
            "model": config.embeddings.azure.model,
            "dimensions": config.embeddings.azure.dimensions,
        }
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


def get_embedding_dimensions(model_name: str = None, provider: str = None) -> int:
    """Get embedding dimensions for a specific model or provider"""
    config = get_config()

    # If specific model is provided, look it up in model_dimensions
    if model_name and model_name in config.model_dimensions:
        return config.model_dimensions[model_name]

    # Otherwise, get dimensions from provider config
    provider = provider or config.defaults.embedding_provider
    embedding_config = get_embedding_config(provider)

    # If no specific model name, try to get dimensions from current model
    if not model_name:
        model_name = embedding_config["model"]
        if model_name in config.model_dimensions:
            return config.model_dimensions[model_name]

    # Fallback to provider's configured dimensions
    return embedding_config["dimensions"]


def get_current_embedding_dimensions() -> int:
    """Get dimensions for the currently configured embedding model"""
    config = get_config()
    provider = config.defaults.embedding_provider

    if provider == "openai":
        model = config.embeddings.openai.model
    elif provider == "ollama":
        model = config.embeddings.ollama.model
    elif provider == "azure":
        model = config.embeddings.azure.model
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")

    return get_embedding_dimensions(model, provider)


if __name__ == "__main__":
    # Test the configuration system
    config = get_config()
    print("Configuration loaded successfully!")
    print(f"Default chat provider: {config.defaults.chat_provider}")
    print(f"Default embedding provider: {config.defaults.embedding_provider}")
    print(f"OpenAI API Key: {'***' if config.openai.api_key else 'Not set'}")
    print(f"Ollama Base URL: {config.ollama.base_url}")
    print(f"Typesense API Key: {'***' if config.typesense.api_key else 'Not set'}")

    # Test embedding dimensions functionality
    print(f"\nEmbedding Configuration:")
    try:
        current_dims = get_current_embedding_dimensions()
        print(f"Current embedding dimensions: {current_dims}")

        # Test specific models
        for model in [
            "text-embedding-3-small",
            "nomic-embed-text",
            "mxbai-embed-large",
        ]:
            dims = get_embedding_dimensions(model)
            print(f"{model}: {dims} dimensions")

    except Exception as e:
        print(f"Error testing embedding dimensions: {e}")

    print(f"\nModel dimensions available: {list(config.model_dimensions.keys())}")
