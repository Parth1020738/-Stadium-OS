# Aegis Smart Stadium OS - Deployment Guide

Step-by-step instructions to deploy Aegis OS.

## Local Docker Compose

To start the system locally with development dependencies:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

## Production Kubernetes Deployment

To deploy onto a Kubernetes cluster (e.g. EKS/GKE):
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/network-policy.yaml
```

## Helm Installation

To deploy using Helm:
```bash
helm install aegis-release ./charts/aegis-os
```
