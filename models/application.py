from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from database.db import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)
    application_text = Column(Text, nullable=False)
    ai_score = Column(Float, nullable=True)
    ai_decision = Column(String(50), nullable=True)  # approve / reject / review
    admin_decision = Column(String(50), nullable=True)  # approve / reject
    status = Column(String(50), default="pending", nullable=False)  # pending / approved / rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
