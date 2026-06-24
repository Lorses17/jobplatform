from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.message import ChatMessage
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.get("/{application_id}", response_model=list[ChatMessageResponse])
async def get_chat_messages(
        application_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить историю сообщений для конкретного отклика."""
    # Извлекаем все сообщения, отсортированные по времени создания
    query = (
        select(ChatMessage)
        .where(ChatMessage.application_id == application_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{application_id}", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
        application_id: int,
        message_in: ChatMessageCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Отправить новое сообщение в чат по отклику."""
    # Роль отправителя берем из текущего авторизованного пользователя
    new_message = ChatMessage(
        application_id=application_id,
        sender_id=current_user.id,
        sender_role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        text=message_in.text
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message