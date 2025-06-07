# TDS Teaching Assistant - Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the TDS Teaching Assistant in a Kubernetes cluster.

## Files

- `namespace.yaml` - Namespace for the application
- `configmap.yaml` - Configuration data
- `secrets.yaml` - Sensitive configuration (template)
- `backend-deployment.yaml` - FastAPI backend deployment
- `backend-service.yaml` - Backend service
- `frontend-deployment.yaml` - Next.js frontend deployment
- `frontend-service.yaml` - Frontend service
- `ingress.yaml` - Ingress configuration
- `typesense.yaml` - Typesense search service
- `kustomization.yaml` - Kustomize configuration

## Quick Start

```bash
# Create namespace and apply all manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml  # Update with your secrets first
kubectl apply -f .

# Or use kustomize
kubectl apply -k .

# Check status
kubectl get pods -n tds-assistant
kubectl get services -n tds-assistant
kubectl get ingress -n tds-assistant
```

## Configuration

1. Update `secrets.yaml` with your actual API keys
2. Modify `configmap.yaml` with your configuration
3. Update `ingress.yaml` with your domain name
4. Adjust resource limits in deployment files as needed

## Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=3 -n tds-assistant

# Scale frontend  
kubectl scale deployment frontend --replicas=2 -n tds-assistant
```
