from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя."""
    # Проверяем, существует ли уже пользователь с таким email
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован",
        )

    # Хэшируем пароль и создаем запись
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login")
async def login(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    # 1. Ищем пользователя по email
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()

    # 2. Проверяем существование пользователя и его пароль
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )

    # 3. ГЕНЕРИРУЕМ НАСТОЯЩИЙ ТОКЕН НА ОСНОВЕ ДАННЫХ ИЗ БД
    # Все строки ниже должны иметь ОДИНАКОВЫЙ отступ (4 пробела от края def)
    user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)

    # Передаем реальный ID и реальную роль пользователя
    access_token = create_access_token(subject=user.id, role=user_role)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }