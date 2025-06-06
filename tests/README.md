# Teaching Assistant Tests

This directory contains all tests for the Teaching Assistant project, organized by test type.

## Directory Structure

```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── unit/                # Unit tests for individual components
├── integration/         # Integration tests for API and services
└── debug/              # Debug scripts and development tests
```

## Test Categories

### Unit Tests (`tests/unit/`)
Tests for individual functions and classes without external dependencies:
- `test_config.py` - Configuration management tests
- `test_spell_check.py` - Spell checking functionality tests
- `test_ocr.py` - OCR processing tests
- `test_batch_embeddings.py` - Batch embedding generation tests
- `test_image_processing.py` - Image processing tests

### Integration Tests (`tests/integration/`)
Tests that verify component interactions and external service integration:
- `test_api_server.py` - API server endpoint tests
- `test_config_integration.py` - End-to-end configuration tests
- `test_enhanced_search.py` - Typesense search functionality tests
- `test_hybrid_multisearch.py` - Multi-search and hybrid search tests

### Debug Scripts (`tests/debug/`)
Development and debugging scripts:
- `debug_ollama.py` - Ollama integration debugging
- `debug_spell_check.py` - Spell check debugging
- `simple_debug.py` - General debugging utilities
- `test_general.py` - General test utilities

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest tests/unit/
```

### Integration Tests Only
```bash
pytest tests/integration/
```

### Specific Test File
```bash
pytest tests/unit/test_config.py
```

### With Coverage
```bash
pytest --cov=api --cov=lib --cov-report=html
```

### Debug Scripts
Debug scripts can be run directly:
```bash
python tests/debug/debug_ollama.py
```

## Test Configuration

- `pytest.ini` - Pytest configuration in the project root
- `conftest.py` - Shared fixtures and test configuration
- Tests use the project's `config.yaml` for configuration

## Prerequisites

1. **Typesense Server**: Required for search-related tests
   ```bash
   ./start_typesense.sh
   ```

2. **API Server**: Required for integration tests
   ```bash
   ./start_server.sh
   ```

3. **Environment Variables**: Set in `.env` file
   - `OPENAI_API_KEY`
   - `TYPESENSE_API_KEY`

## Writing New Tests

### Unit Tests
- Test individual functions/classes
- Mock external dependencies
- Fast execution
- No network calls

### Integration Tests
- Test component interactions
- Use real services when possible
- Slower execution acceptable
- May require external services

### Naming Conventions
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Example Test Structure
```python
import pytest
from unittest.mock import Mock, patch

def test_function_name():
    # Arrange
    input_data = "test input"
    expected_output = "expected result"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output

@pytest.mark.integration
def test_integration_scenario():
    # Integration test example
    pass

@pytest.mark.slow
def test_slow_operation():
    # Mark slow tests
    pass
```
