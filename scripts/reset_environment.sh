#!/bin/bash
# Local environment cleanup utility

echo "Tearing down local infrastructure and purging persistent storage volumes..."

docker compose down -v --rmi local --remove-orphans

echo "Cleanup completed successfully."
