# Installation Guide

Aegis Smart Stadium OS Phase 1 setup instructions.

## Prerequisites

Ensure you have the following installed on your machine:
- Node.js v20.x
- Python v3.11.x
- Docker and Docker Compose
- pnpm package manager (`npm install -g pnpm`)

## Startup Steps

1. **Configure Environment Variables:**
   Copy the example environment variables:
   ```bash
   cp .env.example .env
   ```

2. **Run Monorepo Setup:**
   On Linux/macOS:
   ```bash
   ./scripts/setup.sh
   ```
   On Windows PowerShell:
   ```powershell
   ./scripts/setup.ps1
   ```

3. **Start Local Infrastructure:**
   Deploy databases, message queues, and healthcheck monitors:
   ```bash
   ./scripts/run_local.sh
   ```
   Or on Windows:
   ```powershell
   ./scripts/run_local.ps1
   ```

4. **Verify Health Endpoint Checks:**
   Verify that all service healthchecks return 200:
   - API Gateway health: `curl http://localhost:3000/health`
   - FastAPI health: `curl http://localhost:8000/api/v1/health`
