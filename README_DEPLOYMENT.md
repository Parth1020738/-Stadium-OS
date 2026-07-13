# Aegis Smart Stadium OS - Deployment Documentation

This repository contains deployment configurations for running the Aegis Smart Stadium OS in local development, staging, and enterprise-grade Kubernetes environments.

## Deployment Options

1. **Docker Compose**: Recommended for local development, debugging, and testing. It spins up the relational database, cache, broker, object storage, and full observability tools.
2. **Kubernetes**: Orchestration configuration in `k8s/` for production multi-replica environments.
3. **Helm Charts**: Standard packaging in `charts/aegis-os` for modular installation.
