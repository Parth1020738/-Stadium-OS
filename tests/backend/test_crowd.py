import pytest
import os
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.models.auth import Base
from backend.app.core.security import create_access_token

@pytest.fixture(scope="module", autouse=True)
async def setup_crowd_tables():
    from tests.backend.test_auth import test_engine
    # Ensure user_domain, knowledge, and crowd models are imported to register tables
    import backend.app.models.user_domain
    import backend.app.models.knowledge
    import backend.app.models.crowd
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_crowd_complete_flow():
    # 1. Generate token
    admin_token = create_access_token("admin-crowd-1", ["Admin"])
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # --- Zone CRUD ---
        print("Testing Zone endpoints...")
        res_zone = await ac.post("/api/v1/zones/", json={"name": "West Stand", "description": "West Stand Zone"}, headers=headers_admin)
        assert res_zone.status_code == 201
        zone_id = res_zone.json()["id"]

        # Duplicate zone name check
        res_dup = await ac.post("/api/v1/zones/", json={"name": "West Stand"}, headers=headers_admin)
        assert res_dup.status_code == 400

        # Update Zone Capacity
        res_cap = await ac.post(f"/api/v1/zones/{zone_id}/capacity", json={"max_capacity": 12000, "safe_capacity_limit": 10000}, headers=headers_admin)
        assert res_cap.status_code == 200
        assert res_cap.json()["max_capacity"] == 12000

        # Get Zone details
        res_get = await ac.get(f"/api/v1/zones/{zone_id}", headers=headers_admin)
        assert res_get.status_code == 200
        assert res_get.json()["name"] == "West Stand"

        # --- Camera CRUD ---
        print("Testing Camera endpoints...")
        res_cam = await ac.post("/api/v1/cameras/", json={"device_id": "CAM-202", "name": "West Stand Cam 1", "zone_id": zone_id}, headers=headers_admin)
        assert res_cam.status_code == 201
        cam_id = res_cam.json()["id"]

        # Duplicate device_id check
        res_cam_dup = await ac.post("/api/v1/cameras/", json={"device_id": "CAM-202", "name": "Another Name"}, headers=headers_admin)
        assert res_cam_dup.status_code == 400

        # Update camera health log
        res_health = await ac.post(f"/api/v1/cameras/{cam_id}/health", json={"connectivity_status": "Connected", "latency_ms": 15, "fps": 25.0}, headers=headers_admin)
        assert res_health.status_code == 200
        assert res_health.json()["latency_ms"] == 15

        # --- Telemetry & Thresholds ---
        print("Testing Telemetry & Thresholds...")
        # Create warning thresholds
        res_thresh1 = await ac.post(f"/api/v1/crowd/zones/{zone_id}/thresholds", json={"threshold_type": "OccupancyWarning", "value": 9000.0}, headers=headers_admin)
        assert res_thresh1.status_code == 200

        # Register Crowd Snapshot (triggers warning because count 9500 > 9000.0)
        res_snap = await ac.post("/api/v1/crowd/snapshots", json={"zone_id": zone_id, "camera_id": cam_id, "estimated_count": 9500, "density_level": 1.4}, headers=headers_admin)
        assert res_snap.status_code == 201
        snap_id = res_snap.json()["id"]

        # Duplicate snapshot detection
        res_snap_dup = await ac.post("/api/v1/crowd/snapshots", json={"zone_id": zone_id, "camera_id": cam_id, "estimated_count": 9500, "density_level": 1.4, "recorded_at": res_snap.json()["recorded_at"]}, headers=headers_admin)
        assert res_snap_dup.status_code == 400

        # Verify alert was generated
        res_alerts = await ac.get(f"/api/v1/crowd/zones/{zone_id}/alerts", headers=headers_admin)
        assert res_alerts.status_code == 200
        assert len(res_alerts.json()) >= 1
        alert_id = res_alerts.json()[0]["id"]

        # Resolve alert
        res_resolve = await ac.post(f"/api/v1/crowd/alerts/{alert_id}/resolve", headers=headers_admin)
        assert res_resolve.status_code == 200
        assert res_resolve.json()["resolved_at"] is not None

        # --- Flow calculations ---
        res_ingress = await ac.post(f"/api/v1/crowd/zones/{zone_id}/ingress", json={"turnstile_id": "T-WEST-1", "scan_rate_per_min": 75}, headers=headers_admin)
        assert res_ingress.status_code == 200
        assert res_ingress.json()["scan_rate_per_min"] == 75

        res_egress = await ac.post(f"/api/v1/crowd/zones/{zone_id}/egress", json={"exit_gate_id": "G-WEST-1", "flow_velocity": 1.6, "dispersal_rate_per_min": 50}, headers=headers_admin)
        assert res_egress.status_code == 200
        assert res_egress.json()["flow_velocity"] == 1.6

        # --- Heatmap generation ---
        res_heatmap = await ac.post(f"/api/v1/crowd/zones/{zone_id}/heatmap", json=[{"x": 10, "y": 20, "val": 1.8}], headers=headers_admin)
        assert res_heatmap.status_code == 200
        assert len(res_heatmap.json()) == 1

        # --- Optimistic Locking ---
        # Get fresh version id from zone
        res_zone_fresh = await ac.get(f"/api/v1/zones/{zone_id}", headers=headers_admin)
        version_id = res_zone_fresh.json()["version_id"]

        # Successful update
        res_update = await ac.put(f"/api/v1/crowd/snapshots/{snap_id}?version_id={version_id}", json={"estimated_count": 9800, "density_level": 1.6}, headers=headers_admin)
        assert res_update.status_code == 200

        # Stale update should trigger 409 Conflict
        res_conflict = await ac.put(f"/api/v1/crowd/snapshots/{snap_id}?version_id={version_id}", json={"estimated_count": 9900, "density_level": 1.7}, headers=headers_admin)
        assert res_conflict.status_code == 409
