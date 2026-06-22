from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Создаем асинхронный движок (Engine)
# echo=True полезен на этапе разработки, чтобы видеть SQL-запросы в консоли
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Фабрика для создания асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Базовый класс для будущих SQLAlchemy моделей
class Base(DeclarativeBase):
    pass


# Зависимость (dependency) для FastAPI, которая гарантирует закрытие сессии после запроса
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session