from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Create a dedicated AsyncEngine for Celery tasks using NullPool to avoid connection reuse across event loops
# NullPool disables connection pooling, ensuring fresh connections per task invocation
celery_engine = create_async_engine(
    settings.database_url,
    echo=True,
    future=True,
    poolclass=NullPool
)

# Create a sessionmaker factory bound to the celery_engine
celery_async_session = sessionmaker(
    celery_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Factory function to create new AsyncSession for Celery tasks
def get_celery_session():
    return celery_async_session()