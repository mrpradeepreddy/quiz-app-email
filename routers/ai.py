from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from models.user import User
from models.question import Question
from models.choice import Choice
from schemas.ai import (
    QuestionGenerationRequest,
    QuestionGenerationResponse,
    GeneratedQuestion,
    GeneratedChoice,
    DifficultyLevel
)
from auth.jwt import get_current_user, require_admin
from services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Services"])

@router.post("/generate-questions", response_model=QuestionGenerationResponse)
def generate_questions(
    request: QuestionGenerationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Generate questions using AI (admin only)."""
    try:
        ai_service = AIService()
        generated_questions = ai_service.generate_questions(
            topic=request.topic,
            difficulty=request.difficulty.value,
            count=request.count
        )
        
        return QuestionGenerationResponse(question=generated_questions)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )

@router.post("/generate-questions-and-save")
def generate_and_save_questions(
    request: QuestionGenerationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Generate questions using AI and save them to database (admin only)."""
    try:
        ai_service = AIService()
        generated_questions = ai_service.generate_questions(
            topic=request.topic,
            difficulty=request.difficulty.value,
            count=request.count
        )
        
        saved_questions = []
        
        for gen_question in generated_questions:
            # Create question
            db_question = Question(
                question_text=gen_question.question_text,
                topic=gen_question.topic,
                level=gen_question.level,
                created_by_user_id=current_user.id
            )
            
            db.add(db_question)
            db.flush()
            
            # Create choices
            for choice_data in gen_question.choices:
                db_choice = Choice(
                    choice_text=choice_data.choice_text,
                    iss_correct=choice_data.is_correct,
                    question_id=db_question.id
                )
                db.add(db_choice)
            
            saved_questions.append(db_question)
        
        db.commit()
        
        return {
            "message": f"Successfully generated and saved {len(saved_questions)} questions",
            "questions": generated_questions
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate and save questions: {str(e)}"
        ) 