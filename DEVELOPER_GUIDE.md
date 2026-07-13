# Developer Guide

Aegis Smart Stadium OS development workflows and rules.

## Core Commands

A unified `Makefile` is configured at the root to handle common developer actions:

```bash
# Setup workspaces and verify configuration
make setup

# Run the local infrastructure in the background (Postgres, Redis, Kafka, MinIO, Grafana)
make run-infra

# Tear down the local infrastructure and purge persistent volumes
make reset-env

# Format all Python and TypeScript code
make format

# Run linter checks
make lint

# Run test suites
make test
```

## Quality and Clean Architecture Mandates

1. **Dependency Direction:** Code must point inward. Adapters and drivers depend on domain entities; entities must never import frameworks (e.g. FastAPI, NestJS).
2. **Secrets Security:** Plaintext secrets must never be committed to git. All keys are loaded from environment variables parsed via configuration validators.
3. **JSON Logging:** Standard output logs must use structured JSON to support Kibana/Grafana indexing.
