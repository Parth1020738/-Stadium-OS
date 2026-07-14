import sys
import httpx

def main():
    print("==================================================")
    print("AEGIS SMART STADIUM OS - API HEALTH CHECK")
    print("==================================================")
    
    url = "http://localhost:8000/api/v1/health"
    print(f"Connecting to: {url}...")
    
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            print(f"[OK] Backend health endpoint responded with status: {status.upper()}")
            print(f"     Uptime: {data.get('uptime_seconds')} seconds")
            print(f"     DB status: {data.get('services', {}).get('database')}")
            print(f"     Redis status: {data.get('services', {}).get('redis')}")
            print(f"     Kafka status: {data.get('services', {}).get('kafka')}")
            sys.exit(0)
        else:
            print(f"[FAILED] Healthy check failed with status code: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"[FAILED] Could not connect to backend API: {str(e)}")
        print("         Make sure the backend server is running on port 8000.")
        sys.exit(1)

if __name__ == "__main__":
    main()
