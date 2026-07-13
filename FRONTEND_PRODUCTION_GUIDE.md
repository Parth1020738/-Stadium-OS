# Frontend Production Deployment Guide

This guide details parameters for production deployments of the Aegis frontend.

---

## 1. Environment Configurations

Define the following keys in your `.env.production` file:
*   `NEXT_PUBLIC_API_URL`: Root endpoint of the FastAPI gateway (e.g. `https://api.aegisstadium.com/api/v1`).
*   `NEXT_PUBLIC_WS_URL`: WebSocket endpoint (e.g. `wss://api.aegisstadium.com/ws`).

---

## 2. CI/CD Compilation Pipeline

Deployments should compile the production code:
```bash
# 1. Clear caches
rm -rf .next

# 2. Ingest clean dependencies
npm ci

# 3. Code audit
npm run lint

# 4. Unit verification
npm run test

# 5. Optimized Static Compilation
npm run build
```
The build process generates pre-rendered, type-safe HTML pages under `.next/`, suitable for deployment behind Nginx or on CDNs.
