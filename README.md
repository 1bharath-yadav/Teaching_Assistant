# 🎓 TDS Teaching Assistant

An intelligent AI-powered teaching assistant with RAG (Retrieval-Augmented Generation) capabilities for the TDS course.

## 🌟 **Features**

- **Course Content Retrieval**: Access course materials via natural language queries
- **Question Answering**: Get detailed answers to TDS course-related questions
- **Vector Search**: Utilizes Typesense for fast semantic search capabilities
- **Responsive UI**: Modern, accessible interface for desktop and mobile

## 📁 **Project Structure**

```
TDS_Teaching_Assistant/
├── api/              # Backend FastAPI application
├── assets/           # Static assets including logos
├── data/             # Data processing scripts and pipelines
├── docker/           # Docker configurations
├── docs/             # Documentation files
├── frontend/         # Next.js frontend application
├── kubernetes/       # Kubernetes deployment configurations
├── lib/              # Shared library code
├── logs/             # Application logs
├── scripts/          # Utility scripts
└── tests/            # Test suites
```

## 🚀 **Deployment Options**

### **Option 1: Integrated Deployment (Simple)**
```bash
# Single command startup
./scripts/start_server.sh       # Serves both API and frontend on port 8000
```

### **Option 2: Separate Deployment (Scalable)**
```bash
# Use the management script
./scripts/manage_separate.sh setup    # One-time setup
./scripts/manage_separate.sh dev      # Development mode
./scripts/manage_separate.sh start    # Production mode

# Or manually
./scripts/start_backend.sh           # API server on port 8000
./scripts/start_frontend.sh          # Frontend on port 3000
```

### **Option 3: Docker (Production-Ready)**
```bash
# Separate services with Docker Compose
docker-compose -f docker/docker-compose.separate.yml up

# With reverse proxy
docker-compose -f docker/docker-compose.separate.yml --profile with-nginx up
```

**📖 For detailed deployment information:**
- [Separate Deployment Guide](docs/SEPARATE_DEPLOYMENT.md)
- [Deployment Comparison](docs/DEPLOYMENT_COMPARISON.md)

## ⚡ **Quick Start**

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd TDS_Teaching_Assistant
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**:
   ```bash
   pip install uv
   uv install
   ```

4. **Setup and start**:
   ```bash
   ./scripts/start_typesense.sh         # Start search service
   ./scripts/manage_separate.sh setup   # Setup separate deployment
   ./scripts/manage_separate.sh dev     # Start development servers
   ```

5. **Verify deployment**:
   ```bash
   ./scripts/verify_deployment.sh       # Test all services
   ```

6. **Access the application**:
   - **Frontend**: http://localhost:3000
   - **API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

## 🔧 **Development**

### Backend Development
```bash
cd api
uvicorn main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit
pytest tests/integration
```

## 📚 **Documentation**

- [Configuration Guide](docs/CONFIG_GUIDE.md)
- [Frontend-Backend Integration](docs/FRONTEND_BACKEND_VERIFICATION.md)
- [Model Parameter Guide](docs/MODEL_PARAMETER_INTEGRATION_COMPLETE.md)
- [Unified Search Integration](docs/UNIFIED_SEARCH_INTEGRATION.md)

## 🐳 **Kubernetes Deployment**

The project includes Kubernetes manifests for cloud deployment:

```bash
# Apply Kubernetes configurations
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/backend-service.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml
kubectl apply -f kubernetes/frontend-service.yaml
kubectl apply -f kubernetes/ingress.yaml
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/backend-service.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml
kubectl apply -f kubernetes/frontend-service.yaml
kubectl apply -f kubernetes/ingress.yaml
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