from sqlalchemy import ForeignKey, String, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    experience: Mapped[str] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=True) # Ссылка на PDF в S3/MinIO

    # Отношения
    user: Mapped["User"] = relationship(back_populates="resume")
    applications: Mapped[list["Application"]] = relationship(back_populates="resume", cascade="all, delete-orphan")