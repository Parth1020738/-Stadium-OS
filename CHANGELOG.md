# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-13

### Added
- Monorepo design mapping FastAPI Backend to Next.js Frontend applications.
- Complete 11 Microservices covering authentication, incident management, crowd density, volunteer scheduling, transit metrics, and accessibility routing.
- Observability stack incorporating Grafana, Loki, Prometheus, Promtail, Alertmanager, and Jaeger.
- Production Helm charts and Docker compose configurations.
- Dynamic AI decision recommendations and emergency playbook search.

### Fixed
- Fixed SQLAlchemy Mapper Registry compiling failures in backend model associations.
- Excluded playwright configurations from standard frontend Vitest check routines.
- Corrected HTTPBearer response expectation checks inside dashboard integration test assertions.
- Aligned Next.js build compilation with static Nginx image copy paths.
