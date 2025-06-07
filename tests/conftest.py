"""
Conftest.py for Teaching Assistant tests

This file contains pytest fixtures and configuration for all tests.
"""

import sys
import os
from pathlib import Path
import pytest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "data"))


@pytest.fixture(scope="session")
def project_root():
    """Provide the project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def config_file():
    """Provide the config file path."""
    return PROJECT_ROOT / "config.yaml"


@pytest.fixture(scope="function")
def temp_test_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture(scope="session")
def api_base_url():
    """Provide the API base URL for integration tests."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def typesense_config():
    """Provide Typesense configuration for tests."""
    return {
        "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
        "api_key": os.getenv("TYPESENSE_API_KEY", "xyz"),
        "connection_timeout_seconds": 10,
    }
