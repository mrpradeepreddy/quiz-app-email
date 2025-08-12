from sqlalchemy import Column,String,Integer,ForeignKey,DateTime
from database.connection import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID,ARRAY
import uuid

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    description = Column(String, nullable=True) # Use Text for longer descriptions
    status = Column(String, default="draft", nullable=False)

    # Relationships
    created_by = relationship("User", back_populates="assessments")
    assessment_questions = relationship("AssessmentQuestion", back_populates="assessment", cascade="all,delete-orphan")
    user_assessments = relationship("UserAssessment", back_populates="assessment", cascade="all,delete-orphan")