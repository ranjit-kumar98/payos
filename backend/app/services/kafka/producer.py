import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.core.config import settings

logger = logging.getLogger(__name__)

class KafkaProducerService:
    _instance: Optional["KafkaProducerService"] = None

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._producer: Optional[AIOKafkaProducer] = None
        self._lock: Optional[asyncio.Lock] = None
        self._initialized = True

    def __new__(cls) -> "KafkaProducerService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _initialize_lock(self) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()

    async def _initialize_producer(self) -> None:
        if self._producer is None:
            try:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
                )
                await self._producer.start()
                logger.info("Kafka producer initialized")
            except KafkaError as e:
                logger.error(f"Failed to initialize Kafka producer: {e}")
                self._producer = None

    async def publish(
        self,
        topic: str,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> None:
        await self._initialize_lock()
        async with self._lock:
            if self._producer is None:
                await self._initialize_producer()

        if self._producer is None:
            logger.warning("Kafka producer is not initialized. Event not published.")
            return

        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "correlation_id": correlation_id,
            "payload": payload,
        }

        try:
            logger.info(f"Publishing event to topic {topic}: {event_type}")
            await self._producer.send_and_wait(topic, self._serialize(event))
            logger.info(f"Event published to topic {topic}: {event_type}")
        except KafkaError as e:
            logger.error(f"Failed to publish event to topic {topic}: {e}")

    def _serialize(self, event: Dict[str, Any]) -> bytes:
        import json
        return json.dumps(event).encode("utf-8")

    async def stop(self) -> None:
        if self._producer is not None:
            try:
                await self._producer.stop()
                logger.info("Kafka producer stopped")
            except KafkaError as e:
                logger.error(f"Failed to stop Kafka producer: {e}")
