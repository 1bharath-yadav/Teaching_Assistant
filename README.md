# 🎓 TDS Teaching Assistant

An intelligent AI-powered teaching assistant with RAG (Retrieval-Augmented Generation) capabilities for the TDS course.

## 🚀 **Deployment Options**

### **Option 1: Integrated Deployment (Simple)**
```bash
# Single command startup
./start_server.sh       # Serves both API and frontend on port 8000
```

### **Option 2: Separate Deployment (Scalable)**
```bash
# Use the management script
./manage_separate.sh setup    # One-time setup
./manage_separate.sh dev      # Development mode
./manage_separate.sh start    # Production mode

# Or manually
./start_backend.sh           # API server on port 8000
./start_frontend.sh          # Frontend on port 3000
```

### **Option 3: Docker (Production-Ready)**
```bash
# Separate services with Docker Compose
docker-compose -f docker-compose.separate.yml up

# With reverse proxy
docker-compose -f docker-compose.separate.yml --profile with-nginx up
```

**📖 For detailed deployment information:**
- [Separate Deployment Guide](SEPARATE_DEPLOYMENT.md)
- [Deployment Comparison](DEPLOYMENT_COMPARISON.md)

## ⚡ **Quick Start**

1. **Install dependencies**:
   ```bash
   uv install
   ```

2. **Setup and start**:
   ```bash
   ./start_typesense.sh         # Start search service
   ./manage_separate.sh setup   # Setup separate deployment
   ./manage_separate.sh dev     # Start development servers
   ```

3. **Verify deployment**:
   ```bash
   ./verify_deployment.sh       # Test all services
   ```

4. **Access the application**:
   - **Frontend**: http://localhost:3000
   - **API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

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