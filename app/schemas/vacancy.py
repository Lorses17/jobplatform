from pydantic import BaseModel, Field
from typing import Optional

# --- СХЕМЫ КОМПАНИИ ---
class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255, description="Название компании")
    description: Optional[str] = Field(None, description="Описание компании")
    logo_url: Optional[str] = Field(None, max_length=500, description="Ссылка на логотип")

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


# --- СХЕМЫ ВАКАНСИИ ---
class VacancyBase(BaseModel):
    title: str = Field(..., max_length=255, description="Название вакансии (например, Python Developer)")
    salary_min: Optional[int] = Field(None, ge=0, description="Минимальная зарплата")
    salary_max: Optional[int] = Field(None, ge=0, description="Максимальная зарплата")
    city: str = Field(..., max_length=100, description="Город")
    skills: list[str] = Field(default_factory=list, description="Список ключевых навыков")
    status: str = Field("active", description="Статус вакансии")

class VacancyCreate(VacancyBase):
    pass

class VacancyResponse(VacancyBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True