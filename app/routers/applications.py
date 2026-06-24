from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.resume import Resume
from app.models.vacancy import Vacancy
from app.models.company import Company
from app.models.application import Application, ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate, ApplicationResponse

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_vacancy(
    action_in: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Откликнуться на вакансию (доступно только соискателям с созданным резюме)."""
    if current_user.role != UserRole.SEEKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Только соискатели могут откликаться на вакансии"
        )

    # Ищем резюме соискателя
    resume_result = await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Сначала создайте резюме для отклика"
        )

    # Проверяем существование вакансии
    vacancy_result = await db.execute(select(Vacancy).where(Vacancy.id == action_in.vacancy_id))
    vacancy = vacancy_result.scalar_one_or_none()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена")

    # Проверяем, не откликался ли соискатель на эту вакансию ранее
    existing_result = await db.execute(
        select(Application).where(
            Application.vacancy_id == action_in.vacancy_id,
            Application.resume_id == resume.id
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы уже откликались на эту вакансию")

    new_app = Application(vacancy_id=action_in.vacancy_id, resume_id=resume.id)
    db.add(new_app)
    await db.commit()
    await db.refresh(new_app)
    return new_app


@router.get("/incoming", response_model=list[ApplicationResponse])
async def get_incoming_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Просмотр входящих откликов (доступно работодателям для вакансий их компании)."""
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступно только работодателям")

    # Находим компанию пользователя и отклики на её вакансии
    query = (
        select(Application)
        .join(Vacancy)
        .join(Company)
        .where(Company.owner_id == current_user.id)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Изменение статуса отклика (доступно только владельцу вакансии)."""
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступно только работодателям")

    # Ищем отклик вместе с вакансией и компанией для проверки прав владельца
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.vacancy).selectinload(Vacancy.company))
        .where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отклик не найден")

    if application.vacancy.company.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы не являетесь владельцем этой вакансии")

    application.status = status_update.status
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/my", response_model=list[ApplicationResponse])
async def get_my_applications(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Просмотр собственных откликов соискателя."""
    if current_user.role != UserRole.SEEKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступно только соискателям"
        )

    # 1. Сначала находим резюме соискателя, чтобы узнать его ID
    resume_result = await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    resume = resume_result.scalar_one_or_none()

    if not resume:
        return []

    # 2. Выбираем все отклики, которые привязаны к этому резюме
    query = select(Application).where(Application.resume_id == resume.id)
    result = await db.execute(query)
    return result.scalars().all()