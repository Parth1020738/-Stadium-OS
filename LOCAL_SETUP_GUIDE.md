# Aegis Smart Stadium OS — Local Run & Setup Guide

This guide details the requirements and steps to configure, run, and test the Aegis Smart Stadium OS locally.

## 1. Prerequisites & System Requirements

- **Operating System**: Windows / macOS / Linux
- **Python**: v3.11 or v3.12
- **Node.js**: v20 or v22
- **Database**: SQLite (default, self-contained inside `aegis.db`)
- **Services (Optional / Auto-Fallback)**:
  - **Redis**: Fallback is automatically simulated via in-memory dictionary.
  - **Kafka**: Fallback is automatically simulated via mock modes.

---

## 2. Environment Variables Configuration

Create a `.env` file in the project root (and a corresponding `.env.local` inside `frontend/` directory):

### Monorepo `.env` (Project Root)
```env
# Core Environment Configuration
NODE_ENV=development
PORT=3000

# Database (Local SQLite default)
DATABASE_URL=sqlite:///./aegis.db

# Redis Cache (Mocked automatically if connection fails)
REDIS_URL=redis://localhost:6379/0

# Kafka Events Bus (Mocked automatically if connection fails)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# JWT Security
JWT_SECRET=super-secure-jwt-secret-key-32-chars-long
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# AI Configuration
ENABLE_MOCK_AI=true
AI_PROVIDER=mock
USE_REAL_GEMINI=false
GEMINI_API_KEY=MOCK_MODE
GEMINI_MODEL=gemini-1.5-flash
```

### Frontend `.env.local` (`frontend/`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 3. Step-by-Step Local Startup

### 3.1 Initialize Database
A pre-populated SQLite database is supplied as `aegis.db` in the repository root. To seed a fresh operator profile, run:
```bash
python scripts/seed_db.py
```
This inserts:
- **Operator Account**: `operator@aegis.com`
- **Password**: `password`

### 3.2 Start the Backend API Server
Activate your virtual environment and start the FastAPI service on port `8000`:
```bash
# Windows Power Shell
.venv\Scripts\activate
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 3.3 Start the Frontend Client
Open a separate terminal window, change directory to `frontend/`, install dependencies, and launch:
```bash
cd frontend
npm install
npm run dev
```
The application will launch on: [http://localhost:3000](http://localhost:3000)

---

## 4. Run Automated Browser Verification

To run the automated Playwright/Chromium test suite, execute the following from the `frontend/` directory:
```bash
npx playwright test
```
The test suite will:
1. Open the application.
2. Sign in using test credentials.
3. Visit every page in the system.
4. Interact with forms and buttons.
5. Record console logs, network payloads, and capture screenshots.
6. Export the final results to `browser_logs/verification_results.json`.

---

## 5. Troubleshooting & Fallbacks

- **Kafka Connection Errors**: If Kafka is not running, the backend logs a warning and falls back to a simulated memory queue automatically. No manual setup required.
- **Redis Connection Errors**: If Redis is not running, the caching service utilizes an in-memory dictionary.
- **SQLite Database Locked**: Ensure no concurrent processes are writing to the database file or close active database inspectors.
- **Port Conflicts**: Ensure ports `8000` (FastAPI) and `3000` (Next.js) are not occupied before launching the services.
