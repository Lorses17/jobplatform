from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse
from app.services.s3 import s3_service
import time
router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_200_OK)
async def save_or_update_resume(
        resume_in: ResumeCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Создать или обновить резюме (автоматический Upsert)."""
    if current_user.role != UserRole.SEEKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Работать с резюме могут только соискатели"
        )

    # Ищем, есть ли уже резюме
    result = await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()

    if resume:
        # Если резюme существует — обновляем его поля
        for key, value in resume_in.model_dump().items():
            setattr(resume, key, value)
    else:
        # Если резюме нет — создаем новое
        resume = Resume(**resume_in.model_dump(), user_id=current_user.id)
        db.add(resume)

    await db.commit()
    await db.refresh(resume)
    return resume


@router.get("/me", response_model=ResumeResponse)
async def get_my_resume(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить резюме текущего авторизованного соискателя."""
    result = await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Резюме не найдено"
        )
    return resume


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_resume(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Удалить резюме текущего авторизованного соискателя."""
    result = await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Резюме не найдено")

    await db.delete(resume)
    await db.commit()
    return None


@router.post("/upload-pdf", response_model=ResumeResponse)
async def upload_resume_pdf(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Загрузить PDF-файл для резюме текущего пользователя с уникальным именем."""
    if current_user.role != UserRole.SEEKER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только соискатели могут загружать резюме")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Допускаются только файлы формата PDF")

    result = await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сначала создайте профиль резюме через POST")

    # Генерируем уникальное имя: добавляем текущее время (Unix Timestamp)
    timestamp = int(time.time())
    object_name = f"user_{current_user.id}_resume_{timestamp}.pdf"

    # Загружаем в S3 через наш сервис
    file_url = await s3_service.upload_file(file, object_name)

    # Обновляем ссылку в базе данных
    resume.file_url = file_url
    await db.commit()
    await db.refresh(resume)

    return resume