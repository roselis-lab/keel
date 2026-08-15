from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from keel.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


async def get_session() -> AsyncSession:
    """FastAPI dependency for an async session."""
    async with async_session() as session:
        yield session
