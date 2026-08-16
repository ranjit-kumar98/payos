import logging
import asyncio
from sqlalchemy import select
from app.celery_app import celery_app
from app.db.session import async_session
from app.models import Merchant
from app.services.analytics_service import get_merchant_analytics
from app.services.analytics_cache_service import set_analytics_cache
from app.services.celery_redis_service import celery_redis_client
from app.db.celery_session import get_celery_session

logger = logging.getLogger(__name__)

async def _precompute_analytics():
    logger.info("Starting analytics pre-computation")
    async with get_celery_session() as db:
        try:
            result = await db.execute(
                select(Merchant.id, Merchant.owner_id).where(Merchant.is_active == True)
            )
            merchants = result.all()
        except Exception as e:
            logger.error(f"Failed to fetch active merchants: {e}")
            return

        for merchant_id, owner_id in merchants:
            try:
                logger.info(f"Processing merchant: {merchant_id}")
                analytics = await get_merchant_analytics(db, owner_id)
                if analytics:
                    print(f"About to cache analytics for merchant {merchant_id}")
                    cache_key = f"analytics:overview:{merchant_id}"
                    await set_analytics_cache(cache_key, analytics, expires_seconds=300, redis_instance=celery_redis_client)
                    print(f"Cache complete for merchant {merchant_id}")
                    logger.info(f"Analytics cache updated: {merchant_id}")
            except Exception as e:
                logger.error(f"Error processing merchant {merchant_id}: {e}")

    logger.info("Analytics pre-computation completed")

@celery_app.task(name="app.tasks.analytics.precompute_analytics_task")
def precompute_analytics_task():
    asyncio.run(_precompute_analytics())
   
