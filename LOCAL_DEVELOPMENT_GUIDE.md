# Local Development Guide

## Setup and Ingestion
This project uses Windows command batch scripts and Python helper tools to automate developer workflows.

### Startup Scripts
- **Start Backend**: Double-click `start_backend.bat`. Starts virtualenv environment and boots uvicorn server on port 8000.
- **Start Frontend**: Double-click `start_frontend.bat`. Starts Next.js development server on port 3000.
- **Start All**: Run `start_all.bat`. Orchestrates both frontend and backend concurrently.

### Process Termination
- **Stop All**: Run `stop_all.bat`. Instantly kills all active node and uvicorn processes.

### Validation Scripts
- **Environment Verification**: Run `python verify_environment.py`. Audits local `.env` and SQLite setups.
- **API Health Check**: Run `python health_check.py`. Verifies responsiveness of the FastAPI gateway.
