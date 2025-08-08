from sqlalchemy import Column, Integer, Boolean, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from database.connection import Base


class UserAnswer(Base):
    __tablename__ = "user_answers"
    
    user_assessment_id = Column(Integer, ForeignKey("user_assessments.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_choice_id = Column(Integer, ForeignKey("choices.id"))
    is_correct = Column(Boolean)


    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('user_assessment_id', 'question_id'),
    )

    # Relationships
    user_assessment = relationship("UserAssessment", back_populates="user_answers")
    question = relationship("Question", back_populates="user_answers")
    selected_choice = relationship("Choice", back_populates="user_answers") 