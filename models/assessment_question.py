from sqlalchemy import Column, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from database.connection import Base


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    marks = Column(Integer, nullable=True)

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('assessment_id', 'question_id'),
    )
    

    # Relationships
    assessment = relationship("Assessment", back_populates="assessment_questions")
    question = relationship("Question", back_populates="assessment_questions") 