@echo off
echo Starting Aegis Smart Stadium OS Backend (FastAPI)...
cd /d "%~dp0"
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
