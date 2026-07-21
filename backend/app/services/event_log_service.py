import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models import EventLog

logger = logging.getLogger(__name__)

class EventLogService:
    @staticmethod
    async def save_event(
        db: AsyncSession,
        topic: str,
        event_type: str,
        partition: int,
        offset: int,
        correlation_id: Optional[str],
        payload: dict
    ) -> EventLog:
        event_log = EventLog(
            topic=topic,
            event_type=event_type,
            partition=partition,
            offset=offset,
            correlation_id=correlation_id,
            payload=payload
        )
        try:
            db.add(event_log)
            await db.commit()
            await db.refresh(event_log)
            logger.info(f"Event persisted successfully | Topic: {topic} | Correlation ID: {correlation_id}")
            return event_log
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to persist event | Topic: {topic} | Correlation ID: {correlation_id} | Error: {e}")
            raise