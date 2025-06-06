"""
Client configuration using centralized config system.

This module provides pre-configured clients for OpenAI and Typesense
using the centralized configuration system.
"""

# Import from centralized config
import sys
import os
from pathlib import Path

# Add the Teaching_Assistant root directory to sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.config import get_openai_client, get_typesense_client

# Export the client getters for backward compatibility
__all__ = ["get_openai_client", "get_typesense_client"]
