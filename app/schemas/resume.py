from pydantic import BaseModel, Field
from typing import Optional

class ResumeBase(BaseModel):
    title: str = Field(..., max_length=255, description="Желаемая должность (например, Frontend Developer)")
    skills: list[str] = Field(default_factory=list, description="Список ключевых навыков")
    experience: Optional[str] = Field(None, description="Описание опыта работы")
    file_url: Optional[str] = Field(None, max_length=500, description="Ссылка на PDF-файл резюме в S3")

class ResumeCreate(ResumeBase):
    pass

class ResumeResponse(ResumeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True