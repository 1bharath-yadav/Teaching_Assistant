# Development Guide

This document provides guidelines and information for developers contributing to the TDS Teaching Assistant project.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher
- Docker (optional, for containerized development)
- UV package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git

### Initial Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TDS_Teaching_Assistant
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

   Or manually:
   ```bash
   # Create environment file
   cp .env.example .env
   
   # Install Python dependencies
   uv install
   
   # Install frontend dependencies
   cd frontend && npm install
   ```

3. Start Typesense:
   ```bash
   ./scripts/start_typesense.sh
   ```

### Development Workflow

You can use the provided Makefile commands to simplify development:

```bash
# Start development servers
make dev

# Run tests
make test

# Format code
make format

# Lint code
make lint
```

## Project Architecture

### Backend (API)

The backend is built with FastAPI and follows a modular structure:

- `api/main.py`: Main entry point
- `api/core/`: Core logic and utilities
- `api/handlers/`: API route handlers
- `api/models/`: Data models and schemas
- `api/services/`: Business logic services
- `api/utils/`: Utility functions

### Frontend

The frontend is built with Next.js:

- `frontend/app/`: Next.js application
- `frontend/components/`: React components
- `frontend/public/`: Static assets
- `frontend/styles/`: CSS and style files

### Shared Libraries

Common code is stored in the `lib` directory:

- `lib/config.py`: Configuration management
- `lib/embeddings.py`: Vector embedding utilities

## Coding Standards

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints
- Write docstrings for functions and classes
- Use Black for code formatting
- Use isort for import sorting
- Use flake8 for linting

### JavaScript/TypeScript

- Use ESLint with Airbnb configuration
- Use Prettier for code formatting
- Use TypeScript for type safety

## Testing

### Backend Tests

- Unit tests are in `tests/unit/`
- Integration tests are in `tests/integration/`
- Run tests with `pytest`

### Frontend Tests

- Unit tests are in `frontend/test/unit/`
- Integration tests are in `frontend/test/integration/`
- Run tests with `npm test` in the frontend directory

## Deployment

### Local Development

```bash
# Start development servers
./scripts/manage_separate.sh dev
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.separate.yml up
```

### Kubernetes Deployment

```bash
# Apply Kubernetes configurations
kubectl apply -f kubernetes/
```

## Troubleshooting

### Common Issues

1. **Typesense connection errors**:
   - Make sure Typesense is running: `./scripts/start_typesense.sh`
   - Check if the API key is correct in `.env`

2. **OpenAI API errors**:
   - Check if the API key is valid in `.env`
   - For local development, ensure Ollama is running if using it as a backend

3. **Frontend build errors**:
   - Clear the Next.js cache: `cd frontend && rm -rf .next`
   - Re-install dependencies: `cd frontend && npm install`

### Logs

Check the logs in the `logs/` directory for more information on errors:

- `logs/backend.log`: Backend API logs
- `logs/frontend.log`: Frontend logs
- `logs/typesense.log`: Typesense logs

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please follow the [code of conduct](CODE_OF_CONDUCT.md) when contributing to this project.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Typesense Documentation](https://typesense.org/docs/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
