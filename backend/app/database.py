"""
CampusShield AI — Async Database Engine & Session Management

Uses SQLAlchemy 2.x async engine with asyncpg driver.
Connection pooling is tuned for multi-campus concurrent load.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ── Async engine with connection pool tuned for production ───────────────────
# pool_size=20, max_overflow=40 → supports ~60 concurrent DB connections
# per backend replica, suitable for 10k+ student traffic peaks.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,          # Validate connections before use
    pool_recycle=3600,           # Recycle connections every hour
    echo=settings.APP_DEBUG,     # Log SQL only in debug mode
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,      # Don't expire objects after commit (async-safe)
    autoflush=False,
)


async def init_db():
    """Called on application startup to verify DB connectivity."""
    async with engine.begin() as conn:
        # Tables are managed by Alembic migrations; this just validates the connection.
        await conn.run_sync(lambda c: None)


async def close_db():
    """Called on application shutdown to drain the connection pool."""
    await engine.dispose()


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields a transactional DB session.
    Rolls back on exception, commits on success.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
