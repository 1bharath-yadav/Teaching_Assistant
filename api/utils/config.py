# ******************** configuration management ********************#
"""
Configuration management for the Teaching Assistant API.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ******************** environment setup ********************#
load_dotenv()

# ******************** configuration class ********************#


class Config:
    """Application configuration."""

    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # OpenAI/Ollama settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")

    # Typesense settings
    TYPESENSE_API_KEY = os.getenv("TYPESENSE_API_KEY", "conscious-field")
    TYPESENSE_HOST = os.getenv("TYPESENSE_HOST", "localhost")
    TYPESENSE_PORT = os.getenv("TYPESENSE_PORT", "8108")
    TYPESENSE_PROTOCOL = os.getenv("TYPESENSE_PROTOCOL", "http")

    # Model settings
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma3:4b")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    # Application paths
    BASE_DIR = Path(__file__).parent.parent.parent
    FRONTEND_BUILD_PATH = BASE_DIR / "frontend" / ".next" / "standalone"
    FRONTEND_STATIC_PATH = BASE_DIR / "frontend" / ".next" / "static"
    FRONTEND_PUBLIC_PATH = BASE_DIR / "frontend" / "public"

    # Analytics
    ANALYTICS_OUTPUT_DIR = os.getenv("ANALYTICS_OUTPUT_DIR", "rag_analytics")

    # Spell check settings
    SPELL_CHECK_THRESHOLD = float(os.getenv("SPELL_CHECK_THRESHOLD", 0.4))


config = Config()
