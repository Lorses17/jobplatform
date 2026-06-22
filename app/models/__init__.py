from app.core.database import Base
from app.models.user import User
from app.models.company import Company
from app.models.vacancy import Vacancy
from app.models.resume import Resume
from app.models.application import Application

# Экспортируем Base и все модели для Alembic
__all__ = ["Base", "User", "Company", "Vacancy", "Resume", "Application"]