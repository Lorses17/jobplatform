from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# ДОБАВЛЕН ИМПОРТ update НА СЛУЧАЙ ИСПОЛЬЗОВАНИЯ, ХОТЯ ОБЪЕКТНЫЙ ПОДХОД НАДЕЖНЕЕ
from sqlalchemy import update

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyResponse

router = APIRouter(prefix="/jobs/company", tags=["Companies"])


@router.get("/my", response_model=CompanyResponse)
async def get_my_company(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить компанию текущего авторизованного работодателя."""
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только работодатели имеют доступ к профилю компании"
        )

    result = await db.execute(select(Company).where(Company.owner_id == current_user.id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Компания не зарегистрирована")
    return company


@router.post("", response_model=CompanyResponse)
async def save_or_update_company(
        company_in: CompanyCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Только работодатели могут управлять компанией")

    # 1. Ищем существующую компанию (как в резюме)
    result = await db.execute(select(Company).where(Company.owner_id == current_user.id))
    company = result.scalar_one_or_none()

    if company:
        # 2. ОБНОВЛЕНИЕ (Один в один как в резюме: прямое присвоение полей)
        company.name = company_in.name
        company.description = company_in.description if company_in.description is not None else ""
        company.logo_url = company_in.logo_url
    else:
        # 3. СОЗДАНИЕ
        company = Company(
            owner_id=current_user.id,
            name=company_in.name,
            description=company_in.description if company_in.description is not None else "",
            logo_url=company_in.logo_url
        )
        db.add(company)

    # 4. Сохраняем транзакцию
    await db.commit()

    # Возвращаем объект (FastAPI сам применит response_model)
    return company