from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_employer
from app.models.user import User
from app.models.company import Company
from app.models.vacancy import Vacancy
# Предположим, что модель откликов называется Application. Импортируй её, если нужно:
# from app.models.application import Application

from app.schemas.vacancy import CompanyCreate, CompanyResponse, VacancyCreate, VacancyResponse

# Импортируй схему отклика, если она есть в проекте:
# from app.schemas.application import ApplicationResponse

router = APIRouter(prefix="/jobs", tags=["Vacancies & Companies"])


# --- ЭНДПОИНТЫ КОМПАНИЙ ---

@router.get("/company/my", response_model=CompanyResponse)
async def get_my_company(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_employer)
):
    """Получить профиль компании текущего авторизованного работодателя."""
    result = await db.execute(select(Company).where(Company.owner_id == current_user.id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не зарегистрирована"
        )
    return company


@router.post("/company", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
        company_in: CompanyCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_employer)
):
    """Создать профиль компании или обновить его, если она уже существует."""
    result = await db.execute(select(Company).where(Company.owner_id == current_user.id))
    existing_company = result.scalar_one_or_none()

    if existing_company:
        # Если компания уже есть — обновляем её (Upsert), чтобы не было ошибки 400!
        existing_company.name = company_in.name
        existing_company.description = company_in.description
        if hasattr(company_in, 'logo_url'):
            existing_company.logo_url = company_in.logo_url
        await db.commit()
        return existing_company

    # Если компании нет — создаем новую
    new_company = Company(**company_in.model_dump(), owner_id=current_user.id)
    db.add(new_company)
    await db.commit()
    await db.refresh(new_company)
    return new_company


# --- ЭНДПОИНТЫ ВАКАНСИЙ ---

@router.post("/vacancies", response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
        vacancy_in: VacancyCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_employer)
):
    """Создать новую вакансию (доступно только работодателям, у которых есть компания)."""
    result = await db.execute(select(Company).where(Company.owner_id == current_user.id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала необходимо зарегистрировать профиль компании"
        )

    new_vacancy = Vacancy(**vacancy_in.model_dump(), company_id=company.id)
    db.add(new_vacancy)
    await db.commit()
    await db.refresh(new_vacancy)
    return new_vacancy


@router.get("/vacancies", response_model=list[VacancyResponse])
async def get_vacancies(
        city: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    """Получить список всех активных вакансий (доступно всем, есть фильтр по городу)."""
    query = select(Vacancy).where(Vacancy.status == "active")

    if city:
        query = query.where(Vacancy.city.ilike(f"%{city}%"))

    result = await db.execute(query)
    return result.scalars().all()


# --- ЭНДПОИНТ ПРОСМОТРА ОТКЛИКОВ НА ВАКАНСИИ РАБОТОДАТЕЛЯ ---

@router.get("/vacancies/my/applications")
async def get_my_vacancies_applications(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_employer)
):
    """Получить все отклики соискателей на вакансии текущего работодателя."""
    # 1. Находим компанию юзера
    comp_res = await db.execute(select(Company).where(Company.owner_id == current_user.id))
    company = comp_res.scalar_one_or_none()

    if not company:
        return []

    # 2. Делаем запрос вакансий этой компании вместе с загруженными откликами (relationship)
    # Если у тебя в модели Vacancy прописана связь с откликами (например, applications), то:
    query = (
        select(Vacancy)
        .where(Vacancy.company_id == company.id)
        # Раскомментируй строку ниже, если в модели Vacancy есть связь applications:
        # .options(selectinload(Vacancy.applications))
    )

    result = await db.execute(query)
    vacancies = result.scalars().all()

    # Возвращаем список вакансий, внутри которых фронтенд сможет прочитать отклики
    return vacancies