"""
Client configuration using centralized config system.

This module provides pre-configured clients for OpenAI and Typesense
using the centralized configuration system.
"""

# Import from centralized config
import sys
import os

# Add the Teaching_Assistant root directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from lib.config import get_openai_client, get_typesense_client

# Export the client getters for backward compatibility
__all__ = ["get_openai_client", "get_typesense_client"]
