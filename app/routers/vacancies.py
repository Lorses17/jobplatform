from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_employer
from app.models.user import User
from app.models.company import Company
from app.models.vacancy import Vacancy
from app.schemas.vacancy import CompanyCreate, CompanyResponse, VacancyCreate, VacancyResponse

router = APIRouter(prefix="/jobs", tags=["Vacancies & Companies"])


# --- ЭНДПОИНТЫ КОМПАНИЙ ---

@router.post("/company", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
        company_in: CompanyCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_employer)
):
    """Создать профиль компании (доступно только работодателям, у которых еще нет компании)."""
    # Проверяем, нет ли уже созданной компании у этого пользователя
    result = await db.execute(select(Company).where(Company.owner_id == current_user.id))
    existing_company = result.scalar_one_or_none()

    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже зарегистрировали компанию"
        )

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
    # Вытаскиваем компанию текущего работодателя
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