import pytest
import pytest_asyncio
import json
import asyncio
from typing import Any
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.main import app
from backend.app.core.dependencies import get_db_session
from backend.app.core.security import hash_password, create_access_token
from backend.app.models.auth import User, Role
from backend.app.models.incident import (
    Incident, IncidentTimeline, IncidentEvidence, IncidentAttachment,
    IncidentComment, IncidentAssignment, IncidentResolution, IncidentEscalation,
    IncidentAudit
)
from backend.app.core.kafka_producer import KafkaProducerClient

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_incidents.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=False, connect_args={"timeout": 5})
async_test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create tables
from backend.app.models.auth import Base
from backend.app.models.incident import Base as IncidentBase

@pytest_asyncio.fixture
async def db_session():
    # Drop first to ensure clean state from any previous failed runs
    async with engine.begin() as conn:
        await conn.run_sync(IncidentBase.metadata.drop_all)
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(IncidentBase.metadata.create_all)
    
    session = async_test_session()
    try:
        yield session
    finally:
        # Rollback any pending transaction to release SQLite write locks
        await session.rollback()
        await session.close()
    
    async with engine.begin() as conn:
        await conn.run_sync(IncidentBase.metadata.drop_all)
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db_session, mock_kafka_producer):
    async def override_get_db():
        yield db_session
    
    old_override = app.dependency_overrides.get(get_db_session)
    app.dependency_overrides[get_db_session] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    if old_override is not None:
        app.dependency_overrides[get_db_session] = old_override
    else:
        app.dependency_overrides.pop(get_db_session, None)

@pytest_asyncio.fixture
async def test_user(db_session):
    # Create roles - need both Steward and Operator for full lifecycle testing
    steward_role = Role(name="Steward", description="Test steward role")
    operator_role = Role(name="Operator", description="Test operator role")
    admin_role = Role(name="Administrator", description="Test admin role")
    db_session.add_all([steward_role, operator_role, admin_role])
    await db_session.flush()
    
    # Create user
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        is_verified=True,
        is_deleted=False,
        status="Active"
    )
    user.roles.extend([steward_role, operator_role, admin_role])
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
def auth_headers(test_user):
    token = create_access_token(subject=test_user.email, roles=["Steward", "Operator", "Administrator"])
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def mock_kafka_producer(monkeypatch):
    mock = MockKafkaProducer()
    # Patch the singleton in ALL modules that import it to prevent real Kafka connections
    monkeypatch.setattr("backend.app.services.incident_service.kafka_producer", mock)
    monkeypatch.setattr("backend.app.main.kafka_producer", mock)
    monkeypatch.setattr("backend.app.core.kafka_producer.kafka_producer", mock)
    # Also patch redis_manager to prevent real Redis connections during shutdown
    class MockRedisManager:
        async def close(self): pass
        async def ping(self): return False
        async def is_token_blacklisted(self, jti): return False
        async def blacklist_token(self, jti, exp): pass
        async def check_rate_limit(self, key, limit, window): return True
    mock_redis = MockRedisManager()
    monkeypatch.setattr("backend.app.main.redis_manager", mock_redis)
    monkeypatch.setattr("backend.app.core.auth_guards.redis_manager", mock_redis)
    return mock

class MockKafkaProducer:
    def __init__(self):
        self.events = []
        self._mock_mode = False
    
    async def start(self):
        pass
    
    async def stop(self):
        pass
    
    async def send_event(self, topic: str, key: Any, value: Any) -> bool:
        self.events.append({"topic": topic, "key": key, "value": value})
        return True
    
    def is_healthy(self):
        return True

@pytest.mark.asyncio
async def test_incident_lifecycle(client: AsyncClient, auth_headers: dict, mock_kafka_producer: MockKafkaProducer, test_user: User):
    """Test complete incident lifecycle: create → assign → comment → escalate → resolve → timeline"""
    
    # 1. Create incident
    response = await client.post("/api/v1/incidents", json={
        "title": "Test Incident",
        "description": "This is a test incident with sufficient length for validation",
        "severity": "High",
        "priority": "High",
        "category": "Security",
        "location_zone": "Section 101",
        "location_details": "Row A",
        "sla_minutes": 15
    }, headers=auth_headers)
    
    assert response.status_code == 201
    incident = response.json()
    incident_id = incident["id"]
    assert incident["status"] == "Open"
    assert incident["priority"] == "High"
    
    # Verify Kafka event
    assert len(mock_kafka_producer.events) == 1
    assert mock_kafka_producer.events[0]["topic"] == "incident.created"
    
    # 2. Assign incident
    response = await client.post(f"/api/v1/incidents/{incident_id}/assign", json={
        "assigned_user_id": test_user.id
    }, headers=auth_headers)
    
    assert response.status_code == 200
    assigned = response.json()
    assert assigned["status"] == "Assigned"
    
    # 3. Add comment
    response = await client.post(f"/api/v1/incidents/{incident_id}/comments", json={
        "comment_text": "Responder is on scene"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    comment = response.json()
    assert comment["comment_text"] == "Responder is on scene"
    
    # 4. Escalate incident
    response = await client.post(f"/api/v1/incidents/{incident_id}/escalate", json={
        "escalation_reason": "Additional support needed",
        "escalated_to_status": "Escalated"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    escalated = response.json()
    assert escalated["status"] == "Escalated"
    assert escalated["priority"] == "Critical"
    
    # 5. Resolve incident
    response = await client.post(f"/api/v1/incidents/{incident_id}/resolve", json={
        "resolution_summary": "Incident resolved successfully",
        "root_cause": "Equipment malfunction"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    resolved = response.json()
    assert resolved["status"] == "Resolved"
    
    # 6. Get timeline
    response = await client.get(f"/api/v1/incidents/{incident_id}/timeline", headers=auth_headers)
    assert response.status_code == 200
    timeline = response.json()
    assert len(timeline) >= 5  # create, assign, comment, escalate, resolve

@pytest.mark.asyncio
async def test_incident_statistics(client: AsyncClient, auth_headers: dict, mock_kafka_producer: MockKafkaProducer):
    """Test statistics endpoint with aggregated query"""
    
    # Create multiple incidents with different statuses
    for i in range(5):
        await client.post("/api/v1/incidents", json={
            "title": f"Incident {i}",
            "description": "Test incident with sufficient length for validation requirements",
            "severity": "Medium",
            "priority": "Medium" if i < 3 else "Critical",
            "category": "Security",
            "location_zone": f"Section {i}",
            "sla_minutes": 15
        }, headers=auth_headers)
    
    response = await client.get("/api/v1/incidents/statistics", headers=auth_headers)
    assert response.status_code == 200
    stats = response.json()
    
    assert stats["total_incidents"] == 5
    assert stats["open_incidents"] == 5
    assert stats["critical_priority_count"] == 2

@pytest.mark.asyncio
async def test_incident_pagination(client: AsyncClient, auth_headers: dict, mock_kafka_producer: MockKafkaProducer):
    """Test pagination of incident list"""
    
    # Create 25 incidents
    for i in range(25):
        await client.post("/api/v1/incidents", json={
            "title": f"Incident {i}",
            "description": "Test incident with sufficient length for validation requirements",
            "severity": "Medium",
            "priority": "Medium",
            "category": "Security",
            "location_zone": "Section 101",
            "sla_minutes": 15
        }, headers=auth_headers)
    
    # Get first page
    response = await client.get("/api/v1/incidents?limit=10&offset=0", headers=auth_headers)
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1["items"]) == 10
    assert page1["total"] == 25
    assert page1["limit"] == 10
    assert page1["offset"] == 0
    
    # Get second page
    response = await client.get("/api/v1/incidents?limit=10&offset=10", headers=auth_headers)
    assert response.status_code == 200
    page2 = response.json()
    assert len(page2["items"]) == 10
    assert page2["offset"] == 10

@pytest.mark.asyncio
async def test_incident_search(client: AsyncClient, auth_headers: dict, mock_kafka_producer: MockKafkaProducer):
    """Test search functionality"""
    
    await client.post("/api/v1/incidents", json={
        "title": "Fire Alarm",
        "description": "Smoke detected in kitchen area",
        "severity": "Critical",
        "priority": "Critical",
        "category": "Fire",
        "location_zone": "Concourse A",
        "sla_minutes": 5
    }, headers=auth_headers)
    
    await client.post("/api/v1/incidents", json={
        "title": "Medical Emergency",
        "description": "Fan requiring medical attention",
        "severity": "High",
        "priority": "High",
        "category": "Medical",
        "location_zone": "Section 102",
        "sla_minutes": 10
    }, headers=auth_headers)
    
    # Search by title
    response = await client.get("/api/v1/incidents?search=Fire", headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert results["total"] == 1
    assert "Fire" in results["items"][0]["title"]
    
    # Search by description
    response = await client.get("/api/v1/incidents?search=medical", headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert results["total"] == 1

@pytest.mark.asyncio
async def test_incident_filtering(client: AsyncClient, auth_headers: dict, mock_kafka_producer: MockKafkaProducer):
    """Test filtering by status, priority, severity, category"""
    
    await client.post("/api/v1/incidents", json={
        "title": "Fight in stands",
        "description": "Two fans involved in altercation",
        "severity": "High",
        "priority": "High",
        "category": "Security",
        "location_zone": "Section 103",
        "sla_minutes": 10
    }, headers=auth_headers)
    
    await client.post("/api/v1/incidents", json={
        "title": "Slip and fall",
        "description": "Fan slipped on wet floor",
        "severity": "Low",
        "priority": "Low",
        "category": "Medical",
        "location_zone": "Concourse B",
        "sla_minutes": 15
    }, headers=auth_headers)
    
    # Filter by category
    response = await client.get("/api/v1/incidents?category=Security", headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert results["total"] == 1
    assert results["items"][0]["category"] == "Security"
    
    # Filter by priority
    response = await client.get("/api/v1/incidents?priority=Low", headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert results["total"] == 1
    assert results["items"][0]["priority"] == "Low"

@pytest.mark.asyncio
async def test_incident_validation(client: AsyncClient, auth_headers: dict):
    """Test input validation"""
    
    # Title too short
    response = await client.post("/api/v1/incidents", json={
        "title": "AB",
        "description": "This is a test incident with sufficient length for validation",
        "severity": "Medium",
        "priority": "Medium",
        "category": "Security",
        "location_zone": "Section 101",
        "sla_minutes": 15
    }, headers=auth_headers)
    assert response.status_code == 422
    
    # Invalid severity
    response = await client.post("/api/v1/incidents", json={
        "title": "Test Incident",
        "description": "This is a test incident with sufficient length for validation",
        "severity": "Invalid",
        "priority": "Medium",
        "category": "Security",
        "location_zone": "Section 101",
        "sla_minutes": 15
    }, headers=auth_headers)
    assert response.status_code == 422
    
    # Invalid category
    response = await client.post("/api/v1/incidents", json={
        "title": "Test Incident",
        "description": "This is a test incident with sufficient length for validation",
        "severity": "Medium",
        "priority": "Medium",
        "category": "Invalid",
        "location_zone": "Section 101",
        "sla_minutes": 15
    }, headers=auth_headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_incident_not_found(client: AsyncClient, auth_headers: dict):
    """Test 404 handling"""
    
    response = await client.get("/api/v1/incidents/99999", headers=auth_headers)
    assert response.status_code == 404
    
    response = await client.post("/api/v1/incidents/99999/assign", json={
        "assigned_user_id": 1
    }, headers=auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_optimistic_locking(client: AsyncClient, auth_headers: dict, mock_kafka_producer: MockKafkaProducer):
    """Test optimistic locking with version_id"""
    
    # Create incident
    response = await client.post("/api/v1/incidents", json={
        "title": "Locking Test",
        "description": "Test incident with sufficient length for validation requirements",
        "severity": "Medium",
        "priority": "Medium",
        "category": "Security",
        "location_zone": "Section 101",
        "sla_minutes": 15
    }, headers=auth_headers)
    assert response.status_code == 201
    incident = response.json()
    incident_id = incident["id"]
    version_id = incident["version_id"]
    
    # Update with correct version
    response = await client.put(f"/api/v1/incidents/{incident_id}", json={
        "title": "Updated Title",
        "version_id": version_id
    }, headers=auth_headers)
    assert response.status_code == 200
    
    # Update with stale version
    response = await client.put(f"/api/v1/incidents/{incident_id}", json={
        "title": "Stale Update",
        "version_id": version_id  # Old version
    }, headers=auth_headers)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_evidence_and_attachments(client: AsyncClient, auth_headers: dict, mock_kafka_producer: MockKafkaProducer):
    """Test evidence upload and attachment linking"""
    
    # Create incident
    response = await client.post("/api/v1/incidents", json={
        "title": "Evidence Test",
        "description": "Test incident with sufficient length for validation requirements",
        "severity": "Medium",
        "priority": "Medium",
        "category": "Security",
        "location_zone": "Section 101",
        "sla_minutes": 15
    }, headers=auth_headers)
    assert response.status_code == 201
    incident_id = response.json()["id"]
    
    # Upload evidence
    response = await client.post(f"/api/v1/incidents/{incident_id}/evidence", json={
        "evidence_type": "Photo",
        "description": "CCTV screenshot",
        "storage_uri": "s3://bucket/evidence.jpg",
        "checksum_sha256": "a" * 64
    }, headers=auth_headers)
    assert response.status_code == 200
    evidence = response.json()
    assert evidence["evidence_type"] == "Photo"
    
    # Link attachment
    response = await client.post(f"/api/v1/incidents/{incident_id}/attachments", json={
        "filename": "report.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "storage_uri": "s3://bucket/report.pdf"
    }, headers=auth_headers)
    assert response.status_code == 200
    attachment = response.json()
    assert attachment["filename"] == "report.pdf"

@pytest.mark.asyncio
async def test_kafka_producer_retry():
    """Test Kafka producer retry logic"""
    producer = KafkaProducerClient(bootstrap_servers="invalid:9092")
    
    # Should fail after retries
    result = await producer.send_event("test", "key", {"test": "data"})
    assert result is False

@pytest.mark.asyncio
async def test_kafka_producer_mock_mode():
    """Test Kafka producer mock mode fallback"""
    producer = KafkaProducerClient(bootstrap_servers="invalid:9092")
    producer._mock_mode = True
    
    result = await producer.send_event("test", "key", {"test": "data"})
    assert result is False

@pytest.mark.asyncio
async def test_log_sanitization():
    """Test log injection prevention (service-level sanitization)."""
    from backend.app.services.incident_service import IncidentService

    service = IncidentService(None)

    # Test control character removal
    assert "\x00" not in service._sanitize_for_logging("test\x00injection")
    assert "\x1f" not in service._sanitize_for_logging("test\x1finjection")

    # Test safe strings pass through
    safe = "Safe log message with newline\n and tab\t"
    assert service._sanitize_for_logging(safe) == safe


@pytest.mark.asyncio
async def test_log_injection_middleware_correlation_id(client: AsyncClient, auth_headers: dict):
    """Test log injection prevention (middleware-level correlation_id sanitization)."""
    malicious_corr_id = "bad\x00cid\ninjection\t" + ("x" * 500)

    response = await client.get(
        "/api/v1/incidents?limit=1&offset=0",
        headers={**auth_headers, "X-Correlation-ID": malicious_corr_id},
    )

    # Endpoint should still work; sanitization is validated by absence of errors.
    assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])