# Aegis Smart Stadium OS - CI/CD Pipeline Guide

CI/CD operations and stages description.

## Pipeline Workflow (GitHub Actions)
- **Linting Stage**: Enforces standard style checking (`flake8`).
- **Testing Stage**: Runs the pytest test suite sequentially to prevent database connection conflicts.
- **Docker Build**: Triggers on push events to `main` branch to compile the production multi-stage image.
- **Vulnerability Checks**: Container security scanning via Trivy.
- **Deployment**: Automatic rollout to Kubernetes clusters using Helm.
