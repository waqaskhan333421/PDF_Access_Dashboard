from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PDFCreate(BaseModel):
    title: str
    description: Optional[str] = None


class PDFResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    file_path: str
    uploaded_by: int
    upload_date: Optional[datetime] = None

    class Config:
        from_attributes = True
