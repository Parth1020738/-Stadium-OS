import os
import sys
import subprocess
from pathlib import Path

def check_command(cmd_name, version_flag="--version"):
    """Check if a command is available and return its version."""
    try:
        result = subprocess.run(
            [cmd_name, version_flag],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            return True, version
        return False, "Not found"
    except Exception:
        return False, "Not found"

def main():
    print("==================================================")
    print("AEGIS SMART STADIUM OS - ENVIRONMENT VERIFIER")
    print("==================================================")

    root_dir = Path(__file__).resolve().parent
    env_paths = {
        "Root Environment": root_dir / ".env",
        "Backend Environment": root_dir / "backend" / ".env",
        "Frontend Environment": root_dir / "frontend" / ".env.local"
    }

    all_passed = True

    print("\n[1] ENVIRONMENT FILES")
    print("-" * 50)
    for name, path in env_paths.items():
        if path.exists():
            print(f"[OK] {name} file found at: {path}")
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            keys = [line.split("=")[0].strip() for line in lines if "=" in line and not line.strip().startswith("#")]
            print(f"     Found {len(keys)} defined variables.")
        else:
            print(f"[WARNING] {name} is missing (expected at: {path})")
            all_passed = False

    print("\n[2] RUNTIME TOOLS")
    print("-" * 50)
    
    # Check Python
    py_ok, py_version = check_command("python", "--version")
    if py_ok:
        print(f"[OK] Python: {py_version}")
    else:
        print("[FAIL] Python: Not found (required)")
        all_passed = False

    # Check Node.js
    node_ok, node_version = check_command("node", "--version")
    if node_ok:
        print(f"[OK] Node.js: {node_version}")
    else:
        print("[FAIL] Node.js: Not found (required for frontend)")
        all_passed = False

    # Check npm
    npm_ok, npm_version = check_command("npm", "--version")
    if npm_ok:
        print(f"[OK] npm: {npm_version}")
    else:
        print("[FAIL] npm: Not found (required for frontend)")
        all_passed = False

    # Check pip
    pip_ok, pip_version = check_command("pip", "--version")
    if pip_ok:
        print(f"[OK] pip: {pip_version}")
    else:
        print("[WARNING] pip: Not found (needed for Python dependencies)")

    print("\n[3] DATABASE")
    print("-" * 50)
    db_file = root_dir / "aegis.db"
    if db_file.exists():
        print(f"[OK] SQLite database found at: {db_file}")
    else:
        print("[WARNING] SQLite database (aegis.db) not initialized yet.")

    print("\n[4] DEPENDENCIES")
    print("-" * 50)
    
    # Check backend dependencies
    backend_req = root_dir / "backend" / "requirements.txt"
    if backend_req.exists():
        print(f"[OK] Backend requirements.txt found")
        # Check if virtual environment exists
        venv_paths = [
            root_dir / ".venv",
            root_dir / "backend" / ".venv",
            root_dir / "venv",
        ]
        venv_found = any(p.exists() for p in venv_paths)
        if venv_found:
            print("[OK] Python virtual environment found")
        else:
            print("[WARNING] No Python virtual environment found (.venv)")
    else:
        print("[FAIL] Backend requirements.txt not found")
        all_passed = False

    # Check frontend dependencies
    frontend_node_modules = root_dir / "frontend" / "node_modules"
    if frontend_node_modules.exists():
        print("[OK] Frontend node_modules found")
    else:
        print("[WARNING] Frontend node_modules not found. Run: cd frontend && npm install")

    print("\n[5] PROCESS CHECK")
    print("-" * 50)
    
    # Check if backend is running
    backend_ok, _ = check_command("curl", "--version")
    if backend_ok:
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:8000/api/v1/health", method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    print("[OK] Backend server is running on port 8000")
                else:
                    print("[WARNING] Backend server responded but not healthy")
        except Exception:
            print("[INFO] Backend server not running on port 8000 (start with start_backend.bat)")
    else:
        print("[INFO] curl not available, skipping port checks")

    # Check if frontend is running
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:3000", method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                print("[OK] Frontend dev server is running on port 3000")
            else:
                print("[WARNING] Frontend server responded but not ready")
    except Exception:
        print("[INFO] Frontend dev server not running on port 3000 (start with start_frontend.bat)")

    print("\n" + "=" * 50)
    if all_passed:
        print(">>> System environment check PASSED. Ready for launch. <<<")
        sys.exit(0)
    else:
        print(">>> System environment check DEGRADED. Review warnings above. <<<")
        sys.exit(1)

if __name__ == "__main__":
    main()