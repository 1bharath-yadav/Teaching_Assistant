# API Directory Structure

This directory contains the reorganized Teaching Assistant API with a clean, modular structure.

## Directory Structure

```
api/
├── main.py                 # FastAPI app entry point
├── core/                   # Core business logic
│   ├── __init__.py
│   └── process.py         # Main processing pipeline
├── handlers/               # API route handlers
│   ├── __init__.py
│   └── question_handler.py # Question handling logic
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   └── spell_check.py     # Spell checking utilities
├── analytics/              # Analytics and data collection
│   ├── __init__.py
│   ├── simple_data_collector.py
│   └── rag_analytics/      # RAG analytics data
└── tests/                  # Test modules
    ├── __init__.py
    └── test_optimizations.py
```

## Key Components

### Core (`core/`)
- **process.py**: Contains the main RAG processing pipeline, search functions, and data models

### Handlers (`handlers/`)
- **question_handler.py**: Handles the main question-asking logic, orchestrating spell checking, OCR, and search

### Utils (`utils/`)
- **config.py**: Centralized configuration management using environment variables
- **spell_check.py**: Spell checking and text correction utilities

### Analytics (`analytics/`)
- **simple_data_collector.py**: Collects and exports RAG system analytics
- **rag_analytics/**: Contains analytics data files

## Usage

To start the server with the new organized structure:

```bash
./start_server.sh
```

Or manually:

```bash
unset OPENAI_BASE_URL
unset OPENAI_API_KEY
source .venv/bin/activate
PYTHONPATH="$PWD:$PYTHONPATH" python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Benefits of This Organization

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Easier Testing**: Components can be tested in isolation
3. **Better Maintainability**: Changes to one component don't affect others
4. **Cleaner Imports**: Clear dependency structure
5. **Scalability**: Easy to add new handlers, utilities, or core components

## Configuration

The API now uses a centralized configuration system in `utils/config.py` that reads from environment variables and provides sensible defaults for Ollama usage.
