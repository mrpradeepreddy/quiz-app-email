from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

class Choice(Base):
    __tablename__="choices"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    choice_text = Column(Text, nullable=False)
    iss_correct = Column(Boolean, nullable=False)

    question = relationship("Question", back_populates="choices")
    user_answers = relationship("UserAnswer", back_populates="selected_choice") 