from sqlalchemy import Column,Integer,String,DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
from sqlalchemy.dialects.postgresql import UUID,ARRAY
import uuid
from sqlalchemy.sql import func
from fastapi_mail import ConnectionConfig


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="Student")
    email=Column(String,nullable=False,unique=True,index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    questions = relationship("Question", back_populates="created_by")
    assessments = relationship("Assessment", back_populates="created_by")
    # It represents assessments TAKEN by this user.
    user_assessments = relationship(
        "UserAssessment", 
        foreign_keys="[UserAssessment.user_id]", 
        back_populates="user"
    )

    # ADDED: This new relationship explicitly uses the 'recruiter_id' foreign key.
    # It represents invitations SENT by this user (if they are a recruiter).
    sent_invitations = relationship(
        "UserAssessment", 
        foreign_keys="[UserAssessment.recruiter_id]", 
        back_populates="recruiter"
    )