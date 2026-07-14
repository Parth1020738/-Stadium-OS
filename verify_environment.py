import os
import sys
from pathlib import Path

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

    for name, path in env_paths.items():
        if path.exists():
            print(f"[OK] {name} file found at: {path}")
            # Read variables
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            keys = [line.split("=")[0].strip() for line in lines if "=" in line and not line.strip().startswith("#")]
            print(f"     Found {len(keys)} defined variables.")
        else:
            print(f"[WARNING] {name} is missing (expected at: {path})")
            all_passed = False

    # Check for sqlite database
    db_file = root_dir / "aegis.db"
    if db_file.exists():
        print(f"[OK] SQLite database found at: {db_file}")
    else:
        print("[WARNING] SQLite database (aegis.db) not initialized yet. Run database seeding.")

    if all_passed:
        print("\n>>> System environment check PASSED. Ready for launch. <<<")
        sys.exit(0)
    else:
        print("\n>>> System environment check DEGRADED. Check missing env configs. <<<")
        sys.exit(1)

if __name__ == "__main__":
    main()
