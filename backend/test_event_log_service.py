import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.services.event_log_service import EventLogService
from app.models import EventLog

async def main():
    async with async_session() as session:
        event = await EventLogService.save_event(
            db=session,
            topic="payment.success",
            event_type="payment.success",
            partition=0,
            offset=1,
            correlation_id="test-correlation-id",
            payload={"key": "value"}
        )
        await session.refresh(event)

        if event.id is None:
            raise Exception("Event ID was not generated")
        # Query the event by ID to verify persistence
        result = await session.execute(
            select(EventLog).where(EventLog.id == event.id)
        )
        fetched_event = result.scalars().first()
        if fetched_event is None:
            raise Exception("Failed to fetch the inserted event")
        if fetched_event.topic != "payment.success":
            raise Exception(f"Topic mismatch: expected 'payment.success', got {fetched_event.topic}")
        if fetched_event.event_type != "payment.success":
            raise Exception(f"Event type mismatch: expected 'payment.success', got {fetched_event.event_type}")
        if fetched_event.correlation_id != "test-correlation-id":
            raise Exception(f"Correlation ID mismatch: expected 'test-correlation-id', got {fetched_event.correlation_id}")

        print("====================================")
        print("✅ EventLogService Test Passed")
        print(f"Event ID: {event.id}")
        print(f"Topic: {fetched_event.topic}")
        print("====================================")

if __name__ == "__main__":
    import asyncio
    from sqlalchemy.future import select
    from app.models import EventLog

    asyncio.run(main())
