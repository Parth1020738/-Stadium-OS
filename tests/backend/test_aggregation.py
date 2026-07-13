import pytest
from unittest.mock import AsyncMock, patch
from backend.app.services.aggregation_service import EventAggregationService

@pytest.mark.asyncio
async def test_aggregator_processes_crowd_snapshots():
    aggregator = EventAggregationService(bootstrap_servers="localhost:9092")
    
    mock_redis = AsyncMock()
    with patch("backend.app.services.aggregation_service.redis_manager") as mock_redis_manager:
        mock_redis_manager.client = mock_redis
        
        # Mock keys returning empty list for average density check
        mock_redis.keys.return_value = []
        
        value = {
            "snapshot_id": 42,
            "zone_id": 3,
            "estimated_count": 150,
            "density_level": 2.5
        }
        
        await aggregator._process_message("stadium-crowd-snapshots", b"3", value)
        
        # Verify hset was called on the zone key
        mock_redis.hset.assert_called_once()
        args, kwargs = mock_redis.hset.call_args
        assert args[0] == "stadium:zone:3:crowd"
        assert kwargs["mapping"]["estimated_count"] == "150"
        assert kwargs["mapping"]["density_level"] == "2.5"

@pytest.mark.asyncio
async def test_aggregator_processes_occupancy_updates():
    aggregator = EventAggregationService(bootstrap_servers="localhost:9092")
    
    mock_redis = AsyncMock()
    with patch("backend.app.services.aggregation_service.redis_manager") as mock_redis_manager:
        mock_redis_manager.client = mock_redis
        
        value = {
            "zone_id": 1,
            "occupancy_count": 500
        }
        
        await aggregator._process_message("stadium-occupancy-updates", b"1", value)
        
        # Verify set was called with the occupancy count
        mock_redis.set.assert_called_once_with("stadium:zone:1:occupancy", "500")

@pytest.mark.asyncio
async def test_aggregator_processes_incident_created():
    aggregator = EventAggregationService(bootstrap_servers="localhost:9092")
    
    mock_redis = AsyncMock()
    with patch("backend.app.services.aggregation_service.redis_manager") as mock_redis_manager:
        mock_redis_manager.client = mock_redis
        
        value = {
            "incident_id": 10,
            "title": "Medical emergency",
            "status": "Open",
            "severity": "High",
            "priority": "High",
            "category": "Medical"
        }
        
        await aggregator._process_message("incident.created", b"10", value)
        
        # Verify sadd added incident_id to the active set
        mock_redis.sadd.assert_called_once_with("stadium:incidents:active", "10")
        # Verify incident details written to hash
        mock_redis.hset.assert_called_once()
        args, kwargs = mock_redis.hset.call_args
        assert args[0] == "stadium:incident:10"
        assert kwargs["mapping"]["title"] == "Medical emergency"
