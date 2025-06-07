# 🚀 **TDS Teaching Assistant - Separate Deployment Guide**

This guide covers deploying the TDS Teaching Assistant with **separate backend and frontend services** for better scalability, performance, and maintainability.

## 📋 **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   Typesense     │
│   Frontend      │◄──►│   Backend       │◄──►│   Search        │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8108    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Benefits of Separate Deployment:**
- ✅ **Scalability**: Scale frontend and backend independently
- ✅ **Performance**: Optimized caching and CDN for frontend
- ✅ **Development**: Teams can work independently
- ✅ **Deployment**: Deploy services separately with zero downtime
- ✅ **Monitoring**: Service-specific monitoring and logging

---

## 🛠️ **Quick Start**

### **Option 1: Using Management Script (Recommended)**

```bash
# Setup the project
./manage_separate.sh setup

# Start development servers
./manage_separate.sh dev

# Start production servers
./manage_separate.sh start

# Use Docker (production-ready)
./manage_separate.sh docker
```

### **Option 2: Manual Setup**

```bash
# 1. Start Backend
./start_backend.sh

# 2. Start Frontend (in another terminal)
./start_frontend.sh
```

---

## ⚙️ **Configuration**

### **Backend Configuration (.env.backend)**

```bash
# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEVELOPMENT=false

# Frontend Origins (CORS)
FRONTEND_URL_DEV=http://localhost:3000
FRONTEND_URL_PROD=https://your-domain.com

# LLM Provider
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=http://localhost:11434  # For Ollama

# Search Service
TYPESENSE_URL=http://localhost:8108
TYPESENSE_API_KEY=your_typesense_key
```

### **Frontend Configuration (frontend/.env.production)**

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_ENDPOINT=/api/v1/ask

# Build Configuration
BUILD_MODE=standalone
NODE_ENV=production
PORT=3000
```

---

## 🐳 **Docker Deployment**

### **Development with Docker Compose**

```bash
# Start all services
docker-compose -f docker-compose.separate.yml up

# With Nginx reverse proxy
docker-compose -f docker-compose.separate.yml --profile with-nginx up
```

### **Production Docker Build**

```bash
# Build backend image
docker build -f Dockerfile.backend -t tds-assistant-backend .

# Build frontend image
docker build -f Dockerfile.frontend -t tds-assistant-frontend .

# Run with environment variables
docker run -p 8000:8000 --env-file .env.backend tds-assistant-backend
docker run -p 3000:3000 --env-file frontend/.env.production tds-assistant-frontend
```

---

## 🌐 **Production Deployment Options**

### **1. Traditional VPS/Server**

```bash
# On your server
git clone <your-repo>
cd Teaching_Assistant

# Setup and start
./manage_separate.sh setup
./manage_separate.sh start
```

### **2. Container Orchestration (Kubernetes)**

```yaml
# See kubernetes/ directory for full manifests
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tds-backend
spec:
  replicas: 3
  # ... backend deployment config
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tds-frontend
spec:
  replicas: 2
  # ... frontend deployment config
```

### **3. Cloud Platforms**

#### **AWS**
- **Backend**: ECS/Fargate or Elastic Beanstalk
- **Frontend**: S3 + CloudFront or ECS
- **Database**: RDS + ElastiCache
- **Search**: OpenSearch or self-hosted

#### **Google Cloud**
- **Backend**: Cloud Run or GKE
- **Frontend**: Firebase Hosting or Cloud Run
- **Database**: Cloud SQL + Memorystore
- **Search**: Vertex AI Search or self-hosted

#### **Vercel + Railway/Render**
- **Frontend**: Vercel (optimal for Next.js)
- **Backend**: Railway, Render, or DigitalOcean App Platform

---

## 🔧 **Environment-Specific Configurations**

### **Development**
```bash
# Backend
API_HOST=127.0.0.1
DEVELOPMENT=true
LOG_LEVEL=DEBUG

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NODE_ENV=development
```

### **Staging**
```bash
# Backend
API_HOST=0.0.0.0
DEVELOPMENT=false
LOG_LEVEL=INFO

# Frontend
NEXT_PUBLIC_API_BASE_URL=https://api-staging.yourdomain.com
NODE_ENV=production
```

### **Production**
```bash
# Backend
API_HOST=0.0.0.0
DEVELOPMENT=false
LOG_LEVEL=WARNING

# Frontend
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NODE_ENV=production
```

---

## 🔍 **Monitoring & Health Checks**

### **Health Check Endpoints**

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# API functionality
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'
```

### **Monitoring Integration**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tds-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'tds-frontend'
    static_configs:
      - targets: ['localhost:3000']
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Backend Issues**
```bash
# Check backend logs
./manage_separate.sh logs

# Test backend connectivity
curl http://localhost:8000/health

# Check configuration
curl http://localhost:8000/api/v1/config
```

#### **Frontend Issues**
```bash
# Check build logs
cd frontend && npm run build

# Test API connectivity from frontend
curl http://localhost:3000/api/health

# Check environment variables
echo $NEXT_PUBLIC_API_BASE_URL
```

#### **CORS Issues**
```bash
# Update backend CORS settings in main_api_only.py
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-domain.com"
]
```

### **Performance Optimization**

#### **Backend Optimization**
- Use async/await for all I/O operations
- Implement connection pooling
- Add Redis caching layer
- Use CDN for static assets

#### **Frontend Optimization**
- Enable Next.js Image Optimization
- Implement code splitting
- Use Service Workers for caching
- Configure proper HTTP headers

---

## 📊 **Scaling Considerations**

### **Horizontal Scaling**

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  backend:
    # ... backend config
    deploy:
      replicas: 3
    
  frontend:
    # ... frontend config
    deploy:
      replicas: 2
```

### **Load Balancing**

```nginx
# nginx.conf
upstream backend_pool {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

upstream frontend_pool {
    server frontend1:3000;
    server frontend2:3000;
}
```

---

## 🔐 **Security Best Practices**

### **API Security**
- ✅ HTTPS only in production
- ✅ Rate limiting configured
- ✅ CORS properly configured
- ✅ Input validation on all endpoints
- ✅ Security headers implemented

### **Frontend Security**
- ✅ CSP headers configured
- ✅ No sensitive data in client-side code
- ✅ Secure authentication flow
- ✅ XSS protection enabled

---

## 📚 **Additional Resources**

- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment Options](https://nextjs.org/docs/deployment)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)

---

## 🆘 **Support**

If you encounter issues:

1. **Check the logs**: `./manage_separate.sh logs`
2. **Verify health**: `./manage_separate.sh health`
3. **Review configuration**: Ensure environment variables are set correctly
4. **Test connectivity**: Verify network connections between services

For additional help, please check the troubleshooting section or create an issue in the repository.
