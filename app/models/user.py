import enum
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    SEEKER = "seeker"
    EMPLOYER = "employer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.SEEKER, nullable=False)

    # Отношения (relationships)
    company: Mapped["Company"] = relationship(back_populates="owner", uselist=False)
    resume: Mapped["Resume"] = relationship(back_populates="user", uselist=False)