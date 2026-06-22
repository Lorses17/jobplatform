from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
import jwt

from app.core.config import settings

# --- РАБОТА С ПАРОЛЯМИ ---

def get_password_hash(password: str) -> str:
    """Хэширование пароля с помощью bcrypt."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка соответствия чистого пароля его хэшу."""
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


# --- РАБОТА С JWT ТОКЕНАМИ ---

def create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """Внутренняя функция для сборки JWT токена."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str | Any) -> str:
    """Создание короткоживущего Access токена (в sub передаем ID пользователя)."""
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(data={"sub": str(subject), "type": "access"}, expires_delta=expires)


def create_refresh_token(subject: str | Any) -> str:
    """Создание долгоживущего Refresh токена для обновления Access токена."""
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(data={"sub": str(subject), "type": "refresh"}, expires_delta=expires)


def decode_token(token: str) -> dict[str, Any] | None:
    """Декодирование и валидация токена."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None