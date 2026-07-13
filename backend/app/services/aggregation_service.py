import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from backend.app.core.config import settings
from backend.app.core.redis import redis_manager

logger = logging.getLogger("aggregation_service")

class EventAggregationService:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.topics = [
            "stadium-crowd-snapshots",
            "stadium-occupancy-updates",
            "incident.created",
            "incident.updated"
        ]

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("Event Aggregation Service background task started.")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.consumer:
            await self.consumer.stop()
        logger.info("Event Aggregation Service background task stopped.")

    async def _consume_loop(self):
        retry_delay = 5
        while self._running:
            try:
                self.consumer = AIOKafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id="aegis-command-center-aggregator",
                    auto_offset_reset="earliest",
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    enable_auto_commit=True
                )
                await self.consumer.start()
                logger.info(f"Aggregator Kafka consumer successfully connected to {self.bootstrap_servers}")
                
                async for msg in self.consumer:
                    if not self._running:
                        break
                    try:
                        await self._process_message(msg.topic, msg.key, msg.value)
                    except Exception as e:
                        logger.error(f"Error processing message from topic {msg.topic}: {e}", exc_info=True)
                        
            except KafkaError as e:
                logger.warning(f"Kafka connection error in consumer loop: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff up to 60s
                retry_delay = min(retry_delay * 2, 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected aggregator loop error: {e}. Retrying in {retry_delay}s...", exc_info=True)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

    async def _process_message(self, topic: str, key: Optional[bytes], value: dict):
        logger.debug(f"Processing event from topic={topic}, value={value}")
        key_str = key.decode("utf-8") if key else ""

        if topic == "stadium-crowd-snapshots":
            zone_id = value.get("zone_id")
            if zone_id is not None:
                redis_key = f"stadium:zone:{zone_id}:crowd"
                await redis_manager.client.hset(redis_key, mapping={
                    "snapshot_id": str(value.get("snapshot_id", "")),
                    "estimated_count": str(value.get("estimated_count", 0)),
                    "density_level": str(value.get("density_level", 0.0)),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                # Re-calculate overall average density cache
                await self._update_average_density()

        elif topic == "stadium-occupancy-updates":
            zone_id = value.get("zone_id")
            if zone_id is not None:
                redis_key = f"stadium:zone:{zone_id}:occupancy"
                await redis_manager.client.set(redis_key, str(value.get("occupancy_count", 0)))

        elif topic == "incident.created":
            inc_id = value.get("incident_id")
            if inc_id is not None:
                # Add to set of active incident IDs
                await redis_manager.client.sadd("stadium:incidents:active", str(inc_id))
                # Store full details
                inc_key = f"stadium:incident:{inc_id}"
                await redis_manager.client.hset(inc_key, mapping={
                    "incident_id": str(inc_id),
                    "title": value.get("title", ""),
                    "status": value.get("status", "Open"),
                    "severity": value.get("severity", ""),
                    "priority": value.get("priority", ""),
                    "category": value.get("category", ""),
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                await self._update_dashboard_summary()

        elif topic == "incident.updated":
            inc_id = value.get("incident_id")
            new_status = value.get("status")
            if inc_id is not None:
                if new_status in ["Resolved", "Closed"]:
                    await redis_manager.client.srem("stadium:incidents:active", str(inc_id))
                    await redis_manager.client.delete(f"stadium:incident:{inc_id}")
                else:
                    inc_key = f"stadium:incident:{inc_id}"
                    if await redis_manager.client.exists(inc_key):
                        await redis_manager.client.hset(inc_key, "status", new_status)
                await self._update_dashboard_summary()

    async def _update_average_density(self):
        # Scan keys matching stadium:zone:*:crowd to compute average density
        try:
            keys = await redis_manager.client.keys("stadium:zone:*:crowd")
            if not keys:
                return
            
            total_density = 0.0
            count = 0
            for key in keys:
                density = await redis_manager.client.hget(key, "density_level")
                if density is not None:
                    total_density += float(density)
                    count += 1
            
            if count > 0:
                avg_density = total_density / count
                await redis_manager.client.set("dashboard:metrics:average_density", str(avg_density))
        except Exception as e:
            logger.error(f"Failed to calculate average density: {e}")

    async def _update_dashboard_summary(self):
        try:
            active_incidents = await redis_manager.client.scard("stadium:incidents:active")
            await redis_manager.client.set("dashboard:metrics:active_incidents_count", str(active_incidents))
        except Exception as e:
            logger.error(f"Failed to update dashboard summary count: {e}")


# Singleton instance
event_aggregator = EventAggregationService(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
