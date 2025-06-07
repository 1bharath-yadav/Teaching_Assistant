#!/usr/bin/env python3
# filepath: /home/archer/projects/llm_tests/Teaching_Assistant/scripts/verify_config.py
"""
Verify that configuration changes are properly loaded from config.yaml.
This script loads the configuration and prints key settings to validate changes.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import configuration module
from lib.config import get_config, reload_config


def main():
    """Load and print configuration to verify it's working properly."""
    try:
        # Force reload configuration
        config = reload_config()

        print("\n===== Teaching Assistant Configuration Verification =====\n")

        # Print basic information
        print(f"Application name: {config.app.name}")
        print(f"Version: {config.app.version}")

        # Print search settings
        print("\n--- Search Configuration ---")
        print(f"Typesense API Key: {config.typesense.api_key}")
        print(f"Typesense Host: {config.typesense.nodes[0].host}")
        print(f"Typesense Port: {config.typesense.nodes[0].port}")

        # Print hybrid search settings
        print("\n--- Hybrid Search Configuration ---")
        print(f"Search Strategy: {config.hybrid_search.search_strategy}")
        print(f"Alpha (hybrid balance): {config.hybrid_search.alpha}")
        print(f"Top K results: {config.hybrid_search.top_k}")

        # Print fallback settings
        print("\n--- Fallback Configuration ---")
        print(
            f"Enable keyword search fallback: {config.hybrid_search.fallback.enable_keyword_search}"
        )
        print(
            f"Min results threshold: {config.hybrid_search.fallback.min_results_threshold}"
        )
        print(
            f"No results message: {config.hybrid_search.fallback.error_messages['no_results']}"
        )

        # Print LLM settings
        print("\n--- LLM Configuration ---")
        print(f"Default chat provider: {config.defaults.chat_provider}")
        print(f"Default embedding provider: {config.defaults.embedding_provider}")

        # If using Ollama
        if config.defaults.chat_provider == "ollama":
            print(f"Ollama default model: {config.ollama.default_model}")
            print(f"Ollama base URL: {config.ollama.base_url}")

        # If using OpenAI
        elif config.defaults.chat_provider == "openai":
            print(f"OpenAI default model: {config.openai.default_model}")

        print("\nConfiguration loaded successfully!")

    except Exception as e:
        print(f"Error loading configuration: {e}")
        import traceback

        print(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
