# Local environment cleanup utility (PowerShell)

Write-Host "Tearing down local infrastructure and purging persistent storage volumes..."

docker compose down -v --rmi local --remove-orphans

Write-Host "Cleanup completed successfully." -ForegroundColor Green
