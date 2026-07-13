# Aegis Smart Stadium OS

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/Parth1020738/-Stadium-OS)
[![Tests Status](https://img.shields.io/badge/tests-53%20passed-green)](https://github.com/Parth1020738/-Stadium-OS)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)
[![Release Version](https://img.shields.io/badge/release-v1.0.0-orange)](https://github.com/Parth1020738/-Stadium-OS/releases/tag/v1.0.0)

Aegis Smart Stadium OS is a hybrid edge-to-cloud platform built for automated crowd safety, security dispatch, and real-time operations coordination. Designed for high-concurrency event telemetry, it features real-time zone density analysis, volunteer scheduling, fleet dispatch, accessibility routing, and AI-driven playbook suggestions.

---

## 1. Overview & Architecture

The Aegis platform provides a modular, reliable framework for stadium staff:
- **Real-Time Data Aggestion**: WebSockets ingest camera occupancy and transit metrics continuously.
- **Optimistic Concurrency Guards**: Prevent database record conflicts under high request concurrency.
- **RAG Suggestion Engine**: Automatically parses emergency playbooks (SOP logs) using semantic similarity matching.
- **Command Approval Gateways**: Multi-operator confirmation paths protect critical stadium actions.

```
                   +------------------------+
                   |   Next.js Front-end    |
                   +-----------+------------+
                               | (REST / WebSockets)
                               v
                   +-----------+------------+
                   |    FastAPI Back-end    |
                   +-----+-----------+------+
                         |           |
             (SQLAlchemy)|           | (Redis Cache)
                         v           v
                   +-----+----+ +----+------+
                   | Postgres | |  Redis   |
                   +----------+ +-----------+
```

---

## 2. Technology Stack

- **Backend**: FastAPI (Python 3.11), SQLAlchemy, PostgreSQL (pgvector), Redis (blacklists/caching), Kafka (event brokers).
- **Frontend**: Next.js 16 (App Router, TypeScript), Zustand, TailwindCSS, Vitest.
- **Infrastructure**: Nginx, Docker Compose, Kubernetes, Helm.
- **Observability**: Prometheus, Grafana, Loki, Promtail, Jaeger.

---

## 3. Folder Structure

```
├── backend/                  # FastAPI Backend API Server
├── frontend/                 # Next.js Frontend Dashboard Client
├── shared/                   # Common modules (TypeScript / Python Logger)
├── infrastructure/           # Logging & reverse proxy configurations
├── charts/                   # Helm charts (Kubernetes deployments)
├── k8s/                      # Kubernetes YAML manifest templates
├── tests/                    # Backend regression test suites
├── docs/                     # System architecture specifications
├── scripts/                  # Cleanup and launch commands
└── GITHUB_DEPLOYMENT_REPORT.md
```

---

## 4. Quick Start & Setup

### 4.1 Prerequisites
- Python 3.11+
- Node.js 20+ (with `pnpm` or `npm`)
- Docker & Docker Compose

### 4.2 Environment Variables
Create a local `.env` file in the root directory:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aegis_db
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
JWT_SECRET=super-secret-key-change-in-production
```

### 4.3 Backend Setup
```bash
# Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
alembic upgrade head

# Start API server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 4.4 Frontend Setup
```bash
cd frontend
pnpm install
pnpm run build
pnpm run dev
```

### 4.5 Docker Stack Setup
```bash
docker-compose up -d
```

### 4.6 Kubernetes / Helm Deployment
```bash
helm install aegis-release charts/aegis-os/
```

---

## 5. Testing & Quality Assurance

Run all test suites locally:
```bash
# Backend sequential suite
python tests/backend/run_tests.py

# Frontend unit testing
cd frontend
pnpm run test
```

---

## 6. Screenshots & Interface Preview

*Screenshots and UI mockups demonstrating the Command Console, Crowd Heatmap, and AI recommendation panels are archived in [walkthrough.md](./walkthrough.md).*

---

## 7. License & Authors

- **License**: MIT License
- **Author**: Parth Patel (Parth1020738)
- **Repository**: [https://github.com/Parth1020738/-Stadium-OS](https://github.com/Parth1020738/-Stadium-OS)
