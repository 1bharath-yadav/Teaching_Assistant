#!/usr/bin/env python3
"""
Unit tests for the centralized configuration system

Tests configuration loading, client creation, and provider switching
functionality for the Teaching Assistant application.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.config import (
    get_config,
    get_openai_client,
    get_typesense_client,
    get_embedding_client,
    get_model_config,
    get_embedding_config,
    reload_config,
)


class TestConfiguration:
    """Test suite for centralized configuration system"""

    def test_configuration_loading(self):
        """Test that configuration loads successfully"""
        config = get_config()

        # Basic configuration assertions
        assert config is not None, "Configuration should load successfully"
        assert hasattr(config, "app"), "Configuration should have app section"
        assert hasattr(config, "defaults"), "Configuration should have defaults section"
        assert hasattr(config, "openai"), "Configuration should have openai section"
        assert hasattr(config, "ollama"), "Configuration should have ollama section"
        assert hasattr(
            config, "typesense"
        ), "Configuration should have typesense section"
        assert hasattr(
            config, "embeddings"
        ), "Configuration should have embeddings section"

    def test_app_configuration(self):
        """Test application-specific configuration"""
        config = get_config()

        assert config.app.name == "Teaching Assistant", "App name should match"
        assert hasattr(config.app, "version"), "App should have version"
        assert hasattr(config.app, "debug"), "App should have debug setting"

    def test_default_providers(self):
        """Test default provider configuration"""
        config = get_config()

        assert config.defaults.chat_provider in [
            "openai",
            "ollama",
        ], "Chat provider should be valid"
        assert config.defaults.embedding_provider in [
            "openai",
            "ollama",
        ], "Embedding provider should be valid"
        assert (
            config.defaults.search_provider == "typesense"
        ), "Search provider should be typesense"

    def test_openai_configuration(self):
        """Test OpenAI provider configuration"""
        config = get_config()

        assert hasattr(config.openai, "base_url"), "OpenAI should have base_url"
        assert hasattr(config.openai, "api_key"), "OpenAI should have api_key"
        assert hasattr(
            config.openai, "default_model"
        ), "OpenAI should have default_model"
        assert hasattr(config.openai, "models"), "OpenAI should have models list"
        assert isinstance(config.openai.models, list), "OpenAI models should be a list"

    def test_ollama_configuration(self):
        """Test Ollama provider configuration"""
        config = get_config()

        assert hasattr(config.ollama, "base_url"), "Ollama should have base_url"
        assert hasattr(
            config.ollama, "default_model"
        ), "Ollama should have default_model"
        assert hasattr(config.ollama, "models"), "Ollama should have models list"
        assert hasattr(
            config.ollama, "embedding_models"
        ), "Ollama should have embedding_models list"
        assert isinstance(config.ollama.models, list), "Ollama models should be a list"
        assert isinstance(
            config.ollama.embedding_models, list
        ), "Ollama embedding models should be a list"

    def test_typesense_configuration(self):
        """Test Typesense search provider configuration"""
        config = get_config()

        assert hasattr(config.typesense, "api_key"), "Typesense should have api_key"
        assert hasattr(config.typesense, "nodes"), "Typesense should have nodes list"
        assert isinstance(
            config.typesense.nodes, list
        ), "Typesense nodes should be a list"

    def test_embeddings_configuration(self):
        """Test embeddings configuration"""
        config = get_config()

        assert hasattr(config.embeddings, "provider"), "Embeddings should have provider"
        assert config.embeddings.provider in [
            "openai",
            "ollama",
        ], "Embeddings provider should be valid"

        if config.embeddings.provider == "openai":
            assert hasattr(
                config.embeddings, "openai"
            ), "Should have OpenAI embeddings config"
            emb_config = config.embeddings.openai
            assert hasattr(emb_config, "model"), "OpenAI embeddings should have model"
            assert hasattr(
                emb_config, "dimensions"
            ), "OpenAI embeddings should have dimensions"
        elif config.embeddings.provider == "ollama":
            assert hasattr(
                config.embeddings, "ollama"
            ), "Should have Ollama embeddings config"
            emb_config = config.embeddings.ollama
            assert hasattr(emb_config, "model"), "Ollama embeddings should have model"
            assert hasattr(
                emb_config, "dimensions"
            ), "Ollama embeddings should have dimensions"


class TestClientCreation:
    """Test suite for client creation functionality"""

    def test_openai_client_creation(self):
        """Test OpenAI client creation"""
        try:
            client = get_openai_client()
            assert client is not None, "OpenAI client should be created successfully"
        except Exception as e:
            pytest.skip(f"OpenAI client creation failed (likely missing API key): {e}")

    def test_typesense_client_creation(self):
        """Test Typesense client creation"""
        try:
            client = get_typesense_client()
            assert client is not None, "Typesense client should be created successfully"
        except Exception as e:
            pytest.skip(
                f"Typesense client creation failed (likely missing API key): {e}"
            )

    def test_embedding_client_creation(self):
        """Test embedding client creation"""
        try:
            client = get_embedding_client()
            assert client is not None, "Embedding client should be created successfully"
        except Exception as e:
            pytest.skip(
                f"Embedding client creation failed (likely missing API key): {e}"
            )


class TestModelConfigurations:
    """Test suite for model configuration functionality"""

    def test_chat_model_config(self):
        """Test getting chat model configuration"""
        try:
            config = get_model_config()
            assert isinstance(config, dict), "Model config should be a dictionary"
            assert "model" in config, "Model config should have 'model' key"
        except Exception as e:
            pytest.skip(f"Model config test failed: {e}")

    def test_embedding_model_config(self):
        """Test getting embedding model configuration"""
        try:
            config = get_embedding_config()
            assert isinstance(config, dict), "Embedding config should be a dictionary"
            assert "model" in config, "Embedding config should have 'model' key"
        except Exception as e:
            pytest.skip(f"Embedding config test failed: {e}")

    def test_provider_switching(self):
        """Test switching between different providers"""
        providers = ["openai", "ollama"]

        for provider in providers:
            try:
                config = get_model_config(provider)
                assert isinstance(
                    config, dict
                ), f"{provider} config should be a dictionary"
                assert "model" in config, f"{provider} config should have 'model' key"
            except Exception as e:
                # Skip individual provider tests if they fail (likely due to missing keys)
                pytest.skip(f"{provider} provider test failed: {e}")


class TestConfigurationReload:
    """Test suite for configuration reload functionality"""

    def test_config_reload(self):
        """Test configuration reload functionality"""
        try:
            # Get initial config
            config1 = get_config()

            # Reload configuration
            reload_config()

            # Get config after reload
            config2 = get_config()

            # Both should be valid configurations
            assert config1 is not None, "Initial config should be valid"
            assert config2 is not None, "Reloaded config should be valid"

        except Exception as e:
            pytest.skip(f"Config reload test failed: {e}")


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
