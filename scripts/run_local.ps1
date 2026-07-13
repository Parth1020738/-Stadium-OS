# Local environment startup orchestrator (PowerShell)

Write-Host "Starting local infrastructure databases, queues, and caches..."

# Start compose services in detached mode
docker compose up -d

Write-Host "Waiting for services to report healthy..."

# Loop checks database health status
while ($true) {
    $status = docker inspect -f '{{.State.Health.Status}}' aegis-postgres 2>$null
    if ($status -eq "healthy") {
        break
    }
    Write-Host "Waiting for PostgreSQL database container..."
    Start-Sleep -Seconds 2
}

Write-Host "Local environment is online. Active dashboards:" -ForegroundColor Green
Write-Host "  Grafana: http://localhost:3000 (admin / admin)"
Write-Host "  MinIO Console: http://localhost:9001"
Write-Host "  Prometheus Console: http://localhost:9090"
