from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from models.question import Question
from models.choice import Choice
from schemas.question import QuestionCreate, QuestionUpdate, QuestionBulkCreate
from fastapi import HTTPException


class QuestionService:
    @staticmethod
    def get_question_by_id(db: Session, question_id: int) -> Optional[Question]:
        return db.query(Question).filter(Question.id == question_id).first()
    

    @staticmethod
    def get_questions(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        topic: Optional[str] = None,
        level: Optional[str] = None
    ) -> List[Question]:
        query = db.query(Question)
        
        if topic:
            query = query.filter(Question.topic == topic)
        if level:
            query = query.filter(Question.level == level)
        
        return query.offset(skip).limit(limit).all()
    

    @staticmethod
    def create_question(db: Session, question: QuestionCreate, user_id: int) -> Question:
        # Create question
        db_question = Question(
            question_text=question.question_text,
            topic=question.topic,
            level=question.level,
            created_by_user_id=user_id
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        
        # Create choices
        for choice_data in question.choices:
            db_choice = Choice(
                question_id=db_question.id,
                choice_text=choice_data.choice_text,
                is_correct=choice_data.is_correct
            )
            db.add(db_choice)
        
        db.commit()
        db.refresh(db_question)
        return db_question
    

    @staticmethod
    def bulk_create_questions(db: Session, questions_data: QuestionBulkCreate, user_id: int) -> List[Question]:
        created_questions = []
        
        for question_data in questions_data.questions:
            question = QuestionService.create_question(db, question_data, user_id)
            created_questions.append(question)
        
        return created_questions
    
    @staticmethod
    def update_question(db: Session, question_id: int, question_update: QuestionUpdate) -> Optional[Question]:
        db_question = QuestionService.get_question_by_id(db, question_id)
        if not db_question:
            return None
        
        update_data = question_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_question, field, value)
        
        db.commit()
        db.refresh(db_question)
        return db_question
    

    @staticmethod
    def delete_question(db: Session, question_id: int) -> bool:
        db_question = QuestionService.get_question_by_id(db, question_id)
        if not db_question:
            return False
        
        db.delete(db_question)
        db.commit()
        return True
    
    @staticmethod
    def get_questions_by_ids(db: Session, question_ids: List[int]) -> List[Question]:
        return db.query(Question).filter(Question.id.in_(question_ids)).all()
    
    @staticmethod
    def validate_question_choices(question: QuestionCreate) -> bool:
        """Validate that exactly one choice is marked as correct"""
        correct_choices = [choice for choice in question.choices if choice.is_correct]
        return len(correct_choices) == 1 