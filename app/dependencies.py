from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.schemas.auth import TokenData

# Указываем FastAPI, откуда автоматически забирать токен (из заголовка Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Зависимость для получения текущего аутентифицированного пользователя по JWT-токену.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Декодируем токен
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")

    # Проверяем, что это именно access-токен, а не refresh
    if user_id is None or token_type != "access":
        raise credentials_exception

    token_data = TokenData(user_id=user_id)

    # Ищем пользователя в базе данных
    result = await db.execute(select(User).where(User.id == int(token_data.user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


# --- ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ РОЛЕЙ ---

async def get_current_employer(current_user: User = Depends(get_current_user)) -> User:
    """Проверка, что текущий пользователь является работодателем."""
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Действие доступно только для работодателей"
        )
    return current_user


async def get_current_seeker(current_user: User = Depends(get_current_user)) -> User:
    """Проверка, что текущий пользователь является соискателем."""
    if current_user.role != UserRole.SEEKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Действие доступно только для соискателей"
        )
    return current_user