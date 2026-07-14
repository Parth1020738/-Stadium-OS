@echo off
echo Starting Aegis Smart Stadium OS Frontend (Next.js)...
cd /d "%~dp0frontend"
echo Checking dependencies...
if not exist node_modules (
    echo Dependencies not found. Run install_dependencies.bat first.
    pause
    exit /b 1
)
echo Launching frontend on http://localhost:3000
start /B "" cmd /c "%~dp0frontend\node_modules\.bin\next dev"
echo Frontend launched successfully! Use stop_all.bat to terminate it.
pause