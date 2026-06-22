from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

# Базовые поля пользователя
class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.SEEKER

# Схема для создания (регистрации) пользователя
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Пароль должен быть не менее 6 символов")

# Схема для входа в систему (Login)
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Схема для ответа API (данные, которые возвращаем клиенту)
class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True  # Позволяет Pydantic работать с объектами SQLAlchemy ORM