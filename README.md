# 🎓 TDS Teaching Assistant

An intelligent AI-powered teaching assistant with [RAG (Retrieval-Augmented Generation)](https://en.wikipedia.org/wiki/Retrieval-augmented_generation) capabilities for the [TDS course](https://tds-course.example.com).

## 🌟 **Features**

- **Course Content Retrieval**: Access [course materials](docs/COURSE_CONTENT.md) via natural language queries
- **Question Answering**: Get detailed answers to [TDS course-related questions](docs/FAQ.md)
- **Vector Search**: Utilizes [Typesense](https://typesense.org/) for fast semantic search capabilities
- **Responsive UI**: Modern, accessible interface for [desktop and mobile](docs/UI_GUIDE.md)

## 📁 **Project Structure**

```
TDS_Teaching_Assistant/
├── [api/](api/)              # Backend FastAPI application
├── [assets/](assets/)        # Static assets including logos
├── [data/](data/)            # Data processing scripts and pipelines
├── [docker/](docker/)        # Docker configurations
├── [docs/](docs/)            # Documentation files
├── [frontend/](frontend/)    # Next.js frontend application
├── [kubernetes/](kubernetes/)# Kubernetes deployment configurations
├── [lib/](lib/)              # Shared library code
├── [logs/](logs/)            # Application logs
├── [scripts/](scripts/)      # Utility scripts
└── [tests/](tests/)          # Test suites
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
   git clone https://github.com/1bharath-yadav/Teaching_Assistant.git
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
   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **API**: [http://localhost:8000](http://localhost:8000)
   - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

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

## 🐳 **Kubernetes Deployment**

The project includes [Kubernetes manifests](kubernetes/) for cloud deployment:

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

This project is licensed under the [MIT License](LICENSE).

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.
1. **Fork the repository**:  
   [https://github.com/1bharath-yadav/Teaching_Assistant.git](https://github.com/1bharath-yadav/Teaching_Assistant.git)

2. **Create a new branch for your changes**:
   ```bash
   git checkout -b improvement/your-feature
   ```

3. **Commit your changes**:
   ```bash
   git commit -m "Describe your enhancement or fix"
   ```

4. **Push your branch to your fork**:
   ```bash
   git push origin improvement/your-feature
   ```
5. Open a Pull Request describing your enhancement or fix

## 🧪 **Testing**

The project uses a well-organized test structure:

- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`  
- **All Tests**: `python run_tests.py all`
- **With Coverage**: `python run_tests.py coverage`

See [tests/README.md](tests/README.md) for detailed testing information.

## ⚙️ **Configuration**

Configuration is managed through:
- [`config.yaml`](config.yaml) - Main configuration file
- [`.env`](.env) - Environment variables (API keys, etc.)
- [`lib/config.py`](lib/config.py) - Configuration utilities

For more details, see [CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md).
##  **Acknowledgements**

The frontend is based on [NextChat](https://github.com/ChatGPTNextWeb/NextChat) &mdash; thanks to the authors and contributers for their excellent open-source work!