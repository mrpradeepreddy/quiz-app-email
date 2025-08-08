from sqlalchemy import Column,Integer,ForeignKey,String,Text,DateTime
from database.connection import Base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID,ARRAY
from uuid import uuid4
import uuid
from sqlalchemy.orm import relationship


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_text = Column(Text, nullable=False)
    topic = Column(String, nullable=True)
    level = Column(String, nullable=True)
    marks = Column(Integer, default=1)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    created_by = relationship("User", back_populates="questions")
    choices = relationship("Choice", back_populates="question", cascade="all,delete-orphan")
    assessment_questions = relationship("AssessmentQuestion", back_populates="question", cascade="all,delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="question", cascade="all,delete-orphan")