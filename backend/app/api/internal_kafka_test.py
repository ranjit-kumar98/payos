from fastapi import APIRouter, Depends

from app.services.kafka.producer import KafkaProducerService

router = APIRouter()

@router.post("/internal/test-kafka")
async def test_kafka(producer: KafkaProducerService = Depends(KafkaProducerService)):
    await producer.publish(
        topic="fraud.detected",
        event_type="test.created",
        payload={"message": "hello from Chunk 6"}
    )
    return {"status": "published"}