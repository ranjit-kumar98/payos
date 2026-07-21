import asyncio
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from app.core.config import settings

from app.db.session import async_session
from app.services.event_log_service import EventLogService

logger = logging.getLogger(__name__)

class KafkaConsumerService:
    _instance: Optional["KafkaConsumerService"] = None

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._lock: Optional[asyncio.Lock] = None
        self._task: Optional[asyncio.Task] = None
        self._initialized = True

    def __new__(cls) -> "KafkaConsumerService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _initialize_lock(self) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()

    async def _initialize_consumer(self) -> None:
        if self._consumer is None:
            try:
                self._consumer = AIOKafkaConsumer(
                    "payment.processed",
                    "payment.success",
                    "payment.failed",
                    "fraud.detected",
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id="payos_consumer_group",
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                )
                await self._consumer.start()
                print("Kafka consumer initialized")
            except KafkaError as e:
                print(f"Failed to initialize Kafka consumer: {e}")
                self._consumer = None

    async def start(self) -> None:
        await self._initialize_lock()
        async with self._lock:
            if self._task is None or self._task.done():
                await self._initialize_consumer()
                if self._consumer is not None:
                    self._task = asyncio.create_task(self.consume())
                    print("Kafka consumer started")

    async def consume(self) -> None:
        if self._consumer is None:
            print("Kafka consumer is not initialized. Cannot consume.")
            return
        try:
            async for msg in self._consumer:
                try:
                    event = json.loads(msg.value.decode("utf-8"))
                except json.JSONDecodeError:
                    print(f"Malformed JSON in message at offset {msg.offset} on topic {msg.topic}")
                    continue

                print("=" * 34)
                print("Kafka Event Received")
                print(f"Topic: {msg.topic}")
                print(f"Partition: {msg.partition}")
                print(f"Offset: {msg.offset}")
                print(f"Event Type: {event.get('event_type')}")
                print(f"Correlation ID: {event.get('correlation_id')}")
                print(f"Payload: {event.get('payload')}")
                print("=" * 34)

                # Persist event to database


                try:
                    async with async_session() as session:
                        await EventLogService.save_event(
                            db=session,
                            topic=msg.topic,
                            event_type=event.get('event_type'),
                            partition=msg.partition,
                            offset=msg.offset,
                            correlation_id=event.get('correlation_id'),
                            payload=event.get('payload')
                        )
                        print(f"Kafka event persisted successfully\nTopic: {msg.topic}\nCorrelation ID: {event.get('correlation_id')}")
                except Exception as e:
                    print(f"Failed to persist Kafka event: {e}")

        except KafkaError as e:
            print(f"Kafka consumer error: {e}")
            # Optionally implement reconnect logic here

    async def stop(self) -> None:
        if self._consumer is not None:
            try:
                await self._consumer.stop()
                print("Kafka consumer stopped")
            except KafkaError as e:
                print(f"Failed to stop Kafka consumer: {e}")
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None