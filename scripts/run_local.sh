#!/bin/bash
# Local environment startup orchestrator

echo "Starting local infrastructure databases, queues, and caches..."

# Start compose services in detached mode
docker compose up -d

echo "Waiting for services to report healthy..."

# Loop checks database health status
until [ "`docker inspect -f {{.State.Health.Status}} aegis-postgres`"=="healthy" ]; do
    echo "Waiting for PostgreSQL database container..."
    sleep 2
done

echo "Local environment is online. Active dashboards:"
echo "  Grafana: http://localhost:3000 (admin / admin)"
echo "  MinIO Console: http://localhost:9001"
echo "  Prometheus Console: http://localhost:9090"
