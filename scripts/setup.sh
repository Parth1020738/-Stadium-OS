#!/bin/bash
# Setup script for Aegis Smart Stadium OS Phase 1

echo "Initializing monorepo workspace configurations..."

# Verify package manager exists
if ! command -v pnpm &> /dev/null
then
    echo "Error: pnpm package manager is not installed."
    echo "Please run: npm install -g pnpm"
    exit 1
fi

# Copy environment template if not present
if [ ! -f .env ]; then
    echo "Creating local .env from template..."
    cp .env.example .env
fi

# Install dependencies across all pnpm workspaces
pnpm install

echo "Monorepo workspace dependencies initialized successfully."
