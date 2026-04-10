from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from database.db import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
