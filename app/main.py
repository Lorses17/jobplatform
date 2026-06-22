from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.routers import auth, vacancies, resumes, applications
from app.services.cache import cache_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при старте приложения
    cache_service.init_redis()
    yield
    # Действия при остановке приложения
    if cache_service.redis:
        await cache_service.redis.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API для платформы поиска работы (Job Platform)",
    version="1.0.0",
    lifespan=lifespan  # Подключаем управление жизненным циклом
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(vacancies.router)
app.include_router(resumes.router)
app.include_router(applications.router)

@app.get("/ping", tags=["Health Check"])
async def ping():
    return {"status": "ok", "project": settings.PROJECT_NAME}