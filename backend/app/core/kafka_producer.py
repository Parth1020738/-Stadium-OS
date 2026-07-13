import json
import logging
import asyncio
from typing import Any, Optional
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger("kafka_producer")

class KafkaProducerClient:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self._mock_mode = False
        self._max_retries = 3
        self._retry_delays = [1, 5, 30]  # Exponential backoff in seconds

    async def start(self):
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=self._max_retries,
                enable_idempotence=True  # Exactly-once semantics
            )
            await self.producer.start()
            logger.info(f"Kafka producer started with bootstrap servers: {self.bootstrap_servers}")
        except Exception as e:
            logger.warning(f"Failed to connect to Kafka: {e}. Falling back to mock mode.")
            self._mock_mode = True
            self.producer = None

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    def is_healthy(self) -> bool:
        return self.producer is not None and not self._mock_mode

    async def send_event(self, topic: str, key: Any, value: Any) -> bool:
        """Send event to Kafka with retry logic and graceful fallback.
        
        Args:
            topic: Kafka topic name
            key: Event key (typically incident_id)
            value: Event payload dict
            
        Returns:
            bool: True if sent successfully, False if in mock mode
        """
        if self._mock_mode:
            logger.info(f"[MOCK MODE] Event sent to topic={topic}, key={key}")
            return False

        if not self.producer:
            logger.warning("Kafka producer not initialized. Event not sent.")
            return False

        # Retry with exponential backoff
        for attempt in range(self._max_retries):
            try:
                await self.producer.send_and_wait(topic, value=value, key=key)
                logger.debug(f"Event sent to topic={topic}, key={key}")
                return True
            except KafkaError as e:
                logger.warning(
                    f"Kafka send attempt {attempt + 1}/{self._max_retries} failed: {e}"
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delays[attempt])
                else:
                    logger.error(f"All retry attempts failed for topic={topic}, key={key}")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error sending to Kafka: {e}")
                return False

        return False

    async def get_health_status(self) -> dict:
        return {
            "producer_state": "mock" if self._mock_mode else ("running" if self.producer else "stopped"),
            "broker_availability": not self._mock_mode and self.producer is not None
        }


# Singleton instance
kafka_producer = KafkaProducerClient()