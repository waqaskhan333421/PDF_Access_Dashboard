from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApplicationCreate(BaseModel):
    pdf_id: int
    application_text: str


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    pdf_id: int
    application_text: str
    ai_score: Optional[float] = None
    ai_decision: Optional[str] = None
    admin_decision: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
