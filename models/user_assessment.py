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

class UserAssessment(Base):
    __tablename__ = "user_assessments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # CHANGED: user_id is now nullable. It will be NULL for an invitation
    # until the student registers.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # ADDED: Foreign key to the User who sent the invite (the recruiter).
    # This is how you link the attempt back to the recruiter.
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # ADDED: The email of the student being invited. Nullable for direct attempts.
    student_email = Column(String, index=True, nullable=True)
     # ADDED: The unique link token for the invitation.
    unique_token = Column(String, unique=True, index=True, 
                          default=lambda: uuid.uuid4().hex)
    
    # ADDED: A status field to track the state of the assessment.
    status = Column(Enum(AssessmentStatus), nullable=False, default=AssessmentStatus.INVITED)


    # --- Relationships ---

    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    score = Column(Integer)
    start_time = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    end_time = Column(DateTime(timezone=True),nullable=True)

    # Relationships

     # ADDED: Relationship to the recruiter.
    recruiter = relationship("User", foreign_keys=[recruiter_id])

   # FIXED: Explicitly define foreign_keys to resolve ambiguity.
    user = relationship("User", foreign_keys=[user_id], back_populates="user_assessments")
    
    # FIXED: Explicitly define foreign_keys and add back_populates to link to User.sent_invitations.
    recruiter = relationship("User", foreign_keys=[recruiter_id], back_populates="sent_invitations")
    
    assessment = relationship("Assessment", back_populates="user_assessments")
    user_answers = relationship("UserAnswer", back_populates="user_assessment", cascade="all, delete-orphan") 

    # --- Constraints ---
    # You might want a new constraint to prevent a recruiter from inviting the
    # same student to the same assessment twice.
    __table_args__ = (
        UniqueConstraint('recruiter_id', 'student_email', 'assessment_id', name='unique_invitation'),
    )