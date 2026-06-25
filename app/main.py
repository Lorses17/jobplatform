import sys
import asyncio
import traceback  # Импортируем traceback, чтобы ушла ошибка!
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine  # Импортируем Base и engine из core/database
from app.services.cache import cache_service

from app.routers import auth, vacancies, resumes, applications
from app.routers.companies import router as companies_router
from app.routers.chats import router as chat_router

# Исправление для работы асинхронности на Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация Redis
    cache_service.init_redis()

    # Автоматическое создание всех таблиц в базе данных при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    if cache_service.redis:
        await cache_service.redis.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API для платформы поиска работы (Job Platform)",
    version="1.0.0",
    lifespan=lifespan
)


# Мидлвар для отладки непредвиденных ошибок
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        error_trace = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "details": error_trace.split("\n")
            }
        )


# Настройка CORS для работы с React
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(vacancies.router)
app.include_router(resumes.router)
app.include_router(applications.router)
app.include_router(companies_router)
app.include_router(chat_router)
@app.get("/ping", tags=["Health Check"])
async def ping():
    return {"status": "ok", "project": settings.PROJECT_NAME}