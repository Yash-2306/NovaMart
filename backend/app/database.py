"""Async SQLAlchemy database setup."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all database tables."""
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Check if we need to add columns to conversation_sessions in case DB already existed
        try:
            await conn.execute(text("ALTER TABLE conversation_sessions ADD COLUMN negotiation_turn_count INTEGER DEFAULT 0"))
        except Exception:
            # Column might already exist
            pass
        try:
            await conn.execute(text("ALTER TABLE conversation_sessions ADD COLUMN negotiation_conceded BOOLEAN DEFAULT 0"))
        except Exception:
            # Column might already exist
            pass
        try:
            await conn.execute(text("ALTER TABLE customers ADD COLUMN delivery_address TEXT"))
        except Exception:
            # Column might already exist
            pass


async def close_db() -> None:
    """Dispose the engine connection pool."""
    await engine.dispose()

