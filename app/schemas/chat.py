from pydantic import BaseModel
from datetime import datetime

class ChatMessageCreate(BaseModel):
    text: str

class ChatMessageResponse(BaseModel):
    id: int
    application_id: int
    sender_id: int
    sender_role: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True