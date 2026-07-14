import sys
import httpx
import urllib.request
from datetime import datetime

def check_url(url, name, timeout=5.0):
    """Check if a URL is accessible."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return True, response.status
    except Exception:
        pass
    
    try:
        response = httpx.get(url, timeout=timeout)
        return True, response.status_code
    except Exception:
        return False, 0

def main():
    print("==================================================")
    print("AEGIS SMART STADIUM OS - API HEALTH CHECK")
    print("==================================================")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    all_healthy = True

    print("\n[1] BACKEND API")
    print("-" * 50)
    backend_ok, backend_status = check_url("http://localhost:8000/api/v1/health")
    if backend_ok:
        if backend_status == 200:
            try:
                response = httpx.get("http://localhost:8000/api/v1/health", timeout=5.0)
                data = response.json()
                status = data.get("status", "unknown")
                print(f"[OK] Backend health endpoint responded with status: {status.upper()}")
                print(f"     Uptime: {data.get('uptime_seconds')} seconds")
                print(f"     DB: {data.get('services', {}).get('database', 'unknown')}")
                print(f"     Redis: {data.get('services', {}).get('redis', 'unknown')}")
                print(f"     Kafka: {data.get('services', {}).get('kafka', 'unknown')}")
            except Exception:
                print("[OK] Backend API is running (health check passed)")
        else:
            print(f"[WARNING] Backend responded with status {backend_status}")
            all_healthy = False
    else:
        print("[FAIL] Backend API is not reachable on port 8000")
        print("       Run: start_backend.bat")
        all_healthy = False

    print("\n[2] FRONTEND DEV SERVER")
    print("-" * 50)
    frontend_ok, frontend_status = check_url("http://localhost:3000")
    if frontend_ok:
        if frontend_status in [200, 307, 308]:
            print("[OK] Frontend dev server is running on port 3000")
        else:
            print(f"[WARNING] Frontend responded with status {frontend_status}")
            all_healthy = False
    else:
        print("[FAIL] Frontend dev server is not reachable on port 3000")
        print("       Run: start_frontend.bat")
        all_healthy = False

    print("\n[3] QUICK API ENDPOINT CHECK")
    print("-" * 50)
    
    # Test auth endpoint (public)
    auth_ok, auth_status = check_url("http://localhost:8000/api/v1/auth/stewards-only", timeout=2.0)
    if auth_ok:
        print(f"[OK] Auth endpoint accessible (status: {auth_status})")
    else:
        print("[INFO] Auth endpoint not accessible (expected if backend started recently)")

    print("\n[4] OPTIONAL SERVICES")
    print("-" * 50)
    
    # Check Redis
    redis_ok, _ = check_url("http://localhost:6379", timeout=1.0)
    if not redis_ok:
        print("[INFO] Redis not accessible on port 6379 (optional for local dev)")
    
    # Check PostgreSQL
    postgres_ok, _ = check_url("http://localhost:5432", timeout=1.0)
    if not postgres_ok:
        print("[INFO] PostgreSQL not accessible on port 5432 (using SQLite for local dev)")
    
    # Check Kafka
    kafka_ok, _ = check_url("http://localhost:9092", timeout=1.0)
    if not kafka_ok:
        print("[INFO] Kafka not accessible on port 9092 (optional for local dev)")

    print("\n" + "=" * 50)
    if all_healthy:
        print(">>> All core services are HEALTHY. System is operational.")
        sys.exit(0)
    else:
        print(">>> Some services are DOWN or UNREACHABLE. Review output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()