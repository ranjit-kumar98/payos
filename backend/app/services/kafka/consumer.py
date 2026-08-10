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

    def __new__(cls) -> "KafkaConsumerService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._consumer: Optional[AIOKafkaConsumer] = None
        self._lock: Optional[asyncio.Lock] = None
        self._task: Optional[asyncio.Task] = None
        self._initialized = True

    async def _initialize_lock(self) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()

    async def _initialize_consumer(self) -> None:
        if self._consumer is not None:
            return

        try:
            self._consumer = AIOKafkaConsumer(
                "payment.processed",
                "payment.success",
                "payment.failed",
                "fraud.detected",
                "fraud.flagged",
                "bnpl.loan_created",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="payos_consumer_group",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )

            await self._consumer.start()
            logger.info("Kafka consumer initialized")

        except KafkaError as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            self._consumer = None

    async def start(self) -> None:
        await self._initialize_lock()

        async with self._lock:
            if self._task is None or self._task.done():
                await self._initialize_consumer()

                if self._consumer is not None:
                    self._task = asyncio.create_task(self.consume())
                    logger.info("Kafka consumer started")

    async def consume(self) -> None:
        if self._consumer is None:
            logger.error("Kafka consumer is not initialized")
            return

        try:
            async for msg in self._consumer:

                try:
                    event = json.loads(msg.value.decode("utf-8"))
                except json.JSONDecodeError:
                    logger.error(
                        f"Malformed JSON in message at offset "
                        f"{msg.offset} on topic {msg.topic}"
                    )
                    continue

                logger.info(
                    "Kafka event received: topic=%s partition=%s offset=%s "
                    "event_type=%s correlation_id=%s",
                    msg.topic,
                    msg.partition,
                    msg.offset,
                    event.get("event_type"),
                    event.get("correlation_id"),
                )

                # Persist Kafka event
                try:
                    async with async_session() as session:
                        await EventLogService.save_event(
                            db=session,
                            topic=msg.topic,
                            event_type=event.get("event_type"),
                            partition=msg.partition,
                            offset=msg.offset,
                            correlation_id=event.get("correlation_id"),
                            payload=event.get("payload"),
                        )

                except Exception as e:
                    logger.error(f"Failed to persist Kafka event: {e}")

                # BNPL → Celery
                if event.get("event_type") == "bnpl.loan_created":
                    try:
                        from app.tasks.bnpl_email import (
                            send_bnpl_loan_agreement_email
                        )

                        payload = event.get("payload") or {}

                        task_result = send_bnpl_loan_agreement_email.delay(
                            payload
                        )

                        logger.info(
                            "BNPL email Celery task queued: task_id=%s "
                            "loan_id=%s",
                            task_result.id,
                            payload.get("loan_id"),
                        )

                    except Exception as e:
                        logger.exception(
                            "Failed to queue BNPL email Celery task: %s",
                            e,
                        )

        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")

    async def stop(self) -> None:
        if self._consumer is not None:
            try:
                await self._consumer.stop()
                logger.info("Kafka consumer stopped")
            except KafkaError as e:
                logger.error(f"Failed to stop Kafka consumer: {e}")

        if self._task is not None:
            self._task.cancel()

            try:
                await self._task
            except asyncio.CancelledError:
                pass

            self._task = None