from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None

async def init_db() -> None:
    global engine, async_session_factory
    engine = create_async_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.is_dev,
    )
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def close_db() -> None:
    if engine:
        await engine.dispose()

async def get_session() -> AsyncSession:  # type: ignore[return]
    if async_session_factory is None:
        raise RuntimeError("DB başlatılmamış — init_db() çağrılmamış")
    async with async_session_factory() as session:
        yield session
