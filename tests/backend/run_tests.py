import os
import subprocess
import sys

test_files = [
    "tests/backend/test_accessibility_api.py",
    "tests/backend/test_accessibility_repositories.py",
    "tests/backend/test_accessibility_services.py",
    "tests/backend/test_aggregation.py",
    "tests/backend/test_ai.py",
    "tests/backend/test_ai_api.py",
    "tests/backend/test_ai_command_center.py",
    "tests/backend/test_ai_copilot.py",
    "tests/backend/test_ai_dashboard.py",
    "tests/backend/test_ai_feedback.py",
    "tests/backend/test_ai_prediction.py",
    "tests/backend/test_ai_rag.py",
    "tests/backend/test_ai_repository.py",
    "tests/backend/test_ai_security.py",
    "tests/backend/test_ai_service.py",
    "tests/backend/test_auth.py",
    "tests/backend/test_command_api.py",
    "tests/backend/test_command_approval.py",
    "tests/backend/test_command_audit.py",
    "tests/backend/test_command_kafka.py",
    "tests/backend/test_command_repository.py",
    "tests/backend/test_command_service.py",
    "tests/backend/test_crowd.py",
    "tests/backend/test_dashboard_api.py",
    "tests/backend/test_dashboard_cache.py",
    "tests/backend/test_dashboard_health.py",
    "tests/backend/test_dashboard_metrics.py",
    "tests/backend/test_dashboard_notifications.py",
    "tests/backend/test_dashboard_repository.py",
    "tests/backend/test_dashboard_security.py",
    "tests/backend/test_dashboard_service.py",
    "tests/backend/test_dashboard_timeline.py",
    "tests/backend/test_dashboard_websocket.py",
    "tests/backend/test_health.py",
    "tests/backend/test_incidents.py",
    "tests/backend/test_knowledge.py",
    "tests/backend/test_transit_api.py",
    "tests/backend/test_users.py",
    "tests/backend/test_volunteer_api.py",
    "tests/backend/test_volunteer_repositories.py",
    "tests/backend/test_volunteer_services.py",
]

def clean_dbs():
    db_files = [
        "test.db",
        "test_users.db",
        "test_incidents.db",
        "test_volunteer_api.db",
        "test_volunteer_repos.db",
        "test_volunteer_services.db",
        "test_transit_api.db",
        "test_accessibility_repos.db",
        "test_accessibility_services.db",
        "test_accessibility_api.db",
        "test_command_api.db",
        "test_command_approval.db",
        "test_command_audit.db",
        "test_command_kafka.db",
        "test_command_repo.db",
        "test_command_service.db",
        "test_dashboard_api.db",
        "test_dashboard_cache.db",
        "test_dashboard_hlth.db",
        "test_dashboard_metrics.db",
        "test_dashboard_notif.db",
        "test_dashboard_repo.db",
        "test_dashboard_sec.db",
        "test_dashboard_service.db",
        "test_dashboard_timeline.db",
    ]
    for db in db_files:
        if os.path.exists(db):
            try:
                os.remove(db)
            except Exception as e:
                print(f"Warning: could not delete {db}: {e}")

def main():
    print("Starting clean sequential backend test run...")
    all_passed = True
    
    for test_file in test_files:
        print(f"\n==================================================")
        print(f"Running: {test_file}")
        print(f"==================================================")
        clean_dbs()
        
        # Run pytest as a subprocess
        result = subprocess.run([".venv\\Scripts\\pytest", test_file], capture_output=False)
        if result.returncode != 0:
            print(f"FAILED: {test_file}")
            all_passed = False
        else:
            print(f"PASSED: {test_file}")
            
    if all_passed:
        print("\nALL BACKEND TESTS PASSED CLEANLY!")
        sys.exit(0)
    else:
        print("\nSOME BACKEND TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
