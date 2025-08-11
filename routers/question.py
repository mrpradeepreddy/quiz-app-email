from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from models.user import User
from models.question import Question
from models.choice import Choice
from schemas.question import (
    QuestionCreate, 
    QuestionUpdate, 
    Question as QuestionSchema,
    ChoiceCreate,
    Choice as ChoiceSchema,
    QuestionBulkCreate
)
from auth.jwt import get_current_user, require_admin, require_student

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/bulk", response_model=List[QuestionSchema])
async def create_questions_bulk(
    questions_data: QuestionBulkCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create multiple questions at once (admin only)."""
    created_questions = []
    
    for question_data in questions_data.questions:
        # Validate that at least one choice is correct
        correct_choices = [choice for choice in question_data.choices if choice.iss_correct]
        if not correct_choices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question '{question_data.question_text}' must have at least one correct choice"
            )
        
        # Create question
        db_question = Question(
            question_text=question_data.question_text,
            topic=question_data.topic,
            level=question_data.level,
            created_by_user_id=current_user.id
        )
        
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        
        # Create choices
        for choice_data in question_data.choices:
            db_choice = Choice(
                choice_text=choice_data.choice_text,
                iss_correct=choice_data.iss_correct,
                question_id=db_question.id
            )
            db.add(db_choice)
        
        created_questions.append(db_question)
    
    db.commit()
    return created_questions

@router.get("/", response_model=List[QuestionSchema])
async def get_questions(
    skip: int = 0,
    limit: int = 100,
    topic: Optional[str] = None,
    level: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all questions with optional filtering."""
    query = db.query(Question)
    
    if topic:
        query = query.filter(Question.topic == topic)
    if level:
        query = query.filter(Question.level == level)
    
    questions = query.offset(skip).limit(limit).all()
    return questions

@router.get("/{question_id}", response_model=QuestionSchema)
async def get_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return question

@router.put("/{question_id}", response_model=QuestionSchema)
async def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a question (admin only)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Update fields
    if question_data.question_text is not None:
        question.question_text = question_data.question_text
    if question_data.topic is not None:
        question.topic = question_data.topic
    if question_data.level is not None:
        question.level = question_data.level
    
    db.commit()
    db.refresh(question)
    return question

@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a question (admin only)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}

@router.get("/topics")
async def get_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all unique topics."""
    topics = db.query(Question.topic).distinct().filter(Question.topic.isnot(None)).all()
    return [topic[0] for topic in topics]

@router.get("/levels")
async def get_levels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all unique levels."""
    levels = db.query(Question.level).distinct().filter(Question.level.isnot(None)).all()
    return [level[0] for level in levels]

@router.post("/{question_id}/choices")
async def add_choice_to_question(
    question_id: int,
    choice_data: ChoiceCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Add a choice to a question (admin only)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    db_choice = Choice(
        choice_text=choice_data.choice_text,
        iss_correct=choice_data.iss_correct,
        question_id=question_id
    )
    
    db.add(db_choice)
    db.commit()
    db.refresh(db_choice)
    return db_choice

@router.put("/choices/{choice_id}")
async def update_choice(
    choice_id: int,
    choice_data: ChoiceCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a choice (admin only)."""
    choice = db.query(Choice).filter(Choice.id == choice_id).first()
    if not choice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Choice not found"
        )
    
    choice.choice_text = choice_data.choice_text
    choice.iss_correct = choice_data.iss_correct
    
    db.commit()
    db.refresh(choice)
    return choice

@router.delete("/choices/{choice_id}")
async def delete_choice(
    choice_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a choice (admin only)."""
    choice = db.query(Choice).filter(Choice.id == choice_id).first()
    if not choice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Choice not found"
        )
    
    # Check if this is the only correct choice
    if choice.iss_correct:
        correct_choices = db.query(Choice).filter(
            Choice.question_id == choice.question_id,
            Choice.iss_correct == True
        ).count()
        
        if correct_choices <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the only correct choice"
            )
    
    db.delete(choice)
    db.commit()
    return {"message": "Choice deleted successfully"} 