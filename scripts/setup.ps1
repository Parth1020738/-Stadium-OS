# Setup script for Aegis Smart Stadium OS Phase 1 (PowerShell)

Write-Host "Initializing monorepo workspace configurations..."

# Verify package manager exists
if (-not (Get-Command "pnpm" -ErrorAction SilentlyContinue)) {
    Write-Error "Error: pnpm package manager is not installed."
    Write-Host "Please run: npm install -g pnpm"
    exit 1
}

# Copy environment template if not present
if (-not (Test-Path ".env")) {
    Write-Host "Creating local .env from template..."
    Copy-Item ".env.example" ".env"
}

# Install dependencies across all pnpm workspaces
pnpm install

Write-Host "Monorepo workspace dependencies initialized successfully." -ForegroundColor Green
