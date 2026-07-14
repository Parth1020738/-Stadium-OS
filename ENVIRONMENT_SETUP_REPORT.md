# Environment Setup Report

## Overview
This report documents the standard configuration schema required to run the Aegis Smart Stadium OS in development, test, and production environments.

## Env Templates
The following template files have been verified/updated in the workspace:
1. **Root Configuration (`.env.example`)**: Contains references to ports, SQLite paths, redis, kafka bootstrap servers, JWT algorithms, and MinIO endpoints.
2. **Backend Configuration (`backend/.env.example`)**: Configured specifically for FastAPI app settings, database engine settings, and secret tokens.
3. **Frontend Configuration (`frontend/.env.local.example`)**: Exposes public endpoints (`NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL`) for Next.js Axios client compilation.

## Key Placeholders Included
- `DATABASE_URL`
- `JWT_SECRET`
- `SECRET_KEY`
- `REDIS_URL`
- `KAFKA_URL` (under KAFKA_BOOTSTRAP_SERVERS)
- `BACKEND_URL`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_WS_URL`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_CLIENT_ID`

## Mock Configuration
All AI keys are default configured to use `MOCK_MODE` with `ENABLE_MOCK_AI=true`, ensuring operations run cleanly without paid endpoints.
