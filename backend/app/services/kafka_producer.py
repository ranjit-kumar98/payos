import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional
import traceback

from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

class KafkaProducer:
    _producer: Optional[AIOKafkaProducer] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_producer(cls) -> AIOKafkaProducer:
        async with cls._lock:
            if cls._producer is None:
                cls._producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                )
                await cls._producer.start()
                print("Kafka connected")
            return cls._producer

    @classmethod
    async def publish(cls, topic: str, event: dict):
        try:
            producer = await cls.get_producer()
            print(f"Publishing to topic {topic}...")
            await producer.send_and_wait(topic, event)
            print("Kafka publish successful")
        except Exception:
            print("Kafka publish failed")
            traceback.print_exc()
            raise
