# Teaching Assistant

An intelligent AI-powered teaching assistant with RAG (Retrieval-Augmented Generation) capabilities.

## Quick Start

1. **Install dependencies**:
   ```bash
   uv install
   ```

2. **Start services**:
   ```bash
   ./start_typesense.sh    # Start Typesense server
   ./start_server.sh       # Start API server
   ```

3. **Run tests**:
   ```bash
   python run_tests.py all
   ```

## Project Structure

```
├── api/                 # FastAPI application
├── data/               # Data processing and RAG pipeline
├── frontend/           # Next.js web interface
├── lib/                # Shared utilities and configuration
├── tests/              # Organized test suite
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── debug/         # Debug scripts
└── typesense-data/    # Typesense database files
```

## Testing

The project uses a well-organized test structure:

- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`  
- **All Tests**: `python run_tests.py all`
- **With Coverage**: `python run_tests.py coverage`

See `tests/README.md` for detailed testing information.

## Configuration

Configuration is managed through:
- `config.yaml` - Main configuration file
- `.env` - Environment variables (API keys, etc.)
- `lib/config.py` - Configuration utilities

## Development

1. **Code Style**: Follow PEP 8
2. **Testing**: Write tests for new features
3. **Documentation**: Update README files as needed

For more details, see `CONFIG_GUIDE.md`.