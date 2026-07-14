@echo off
echo Launching Aegis Smart Stadium OS (Backend + Frontend)...
cd /d "%~dp0"
start "Aegis Backend" cmd /c "%~dp0start_backend.bat"
start "Aegis Frontend" cmd /c "%~dp0start_frontend.bat"
echo Aegis OS services launched successfully! Use stop_all.bat to terminate them.
timeout /t 5
