from pydantic import BaseModel
from app.models.application import ApplicationStatus

class ApplicationCreate(BaseModel):
    vacancy_id: int

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus

class ApplicationResponse(BaseModel):
    id: int
    vacancy_id: int
    resume_id: int
    status: ApplicationStatus

    class Config:
        from_attributes = True