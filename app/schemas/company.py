from pydantic import BaseModel
from typing import Optional

# Тот объект, который прилетает С ФРОНТЕНДА (здесь НЕ должно быть id и owner_id!)
class CompanyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

# Тот объект, который бэкенд ОТДАЕТ НА ФРОНТЕНД
class CompanyResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True