from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint,Enum,String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import uuid
import enum


class AssessmentStatus(str, enum.Enum):
    INVITED = "Invited"
    STARTED = "Started"
    COMPLETED = "Completed"
    # A status for when a registered user takes it directly
    DIRECT_ATTEMPT = "Direct Attempt"

# In file: models/user_assessment.py

class UserAssessment(Base):
    __tablename__ = "user_assessments"
     
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    student_email = Column(String, index=True, nullable=True)
    unique_token = Column(String, unique=True, index=True, default=lambda: uuid.uuid4().hex)
    status = Column(Enum(AssessmentStatus), nullable=False, default=AssessmentStatus.INVITED)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    score = Column(Integer)
    start_time = Column(DateTime(timezone=True), nullable=True) # Removed server_default
    end_time = Column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    user = relationship("User", foreign_keys=[user_id], back_populates="user_assessments")
    recruiter = relationship("User", foreign_keys=[recruiter_id], back_populates="sent_invitations")
    assessment = relationship("Assessment", back_populates="user_assessments")
    user_answers = relationship("UserAnswer", back_populates="user_assessment", cascade="all, delete-orphan") 

    # --- Constraints ---
    __table_args__ = (
        UniqueConstraint('recruiter_id', 'student_email', 'assessment_id', name='unique_invitation'),
    )