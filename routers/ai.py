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
            db.commit()
            db.refresh(db_question)
            
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

@router.post("/analyze-question")
async def analyze_question(
    question_text: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Analyze a question using AI (admin only)."""
    try:
        ai_service = AIService()
        analysis = await ai_service.analyze_question(question_text)
        
        return {
            "question_text": question_text,
            "analysis": analysis
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze question: {str(e)}"
        )

@router.post("/improve-question/{question_id}")
async def improve_question(
    question_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Improve an existing question using AI (admin only)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    try:
        ai_service = AIService()
        improved_question = await ai_service.improve_question(question.question_text)
        
        return {
            "original_question": question.question_text,
            "improved_question": improved_question
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve question: {str(e)}"
        )

@router.post("/suggest-topics")
async def suggest_topics(
    subject: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get AI suggestions for topics (admin only)."""
    try:
        ai_service = AIService()
        topics = await ai_service.suggest_topics(subject)
        
        return {
            "subject": subject,
            "suggested_topics": topics
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest topics: {str(e)}"
        )

@router.post("/validate-question")
async def validate_question(
    question_text: str,
    choices: List[str],
    correct_answer: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Validate a question using AI (admin only)."""
    try:
        ai_service = AIService()
        validation = await ai_service.validate_question(
            question_text=question_text,
            choices=choices,
            correct_answer=correct_answer
        )
        
        return {
            "question_text": question_text,
            "validation": validation
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate question: {str(e)}"
        )

@router.get("/ai-status")
async def get_ai_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check AI service status."""
    try:
        ai_service = AIService()
        status = await ai_service.check_status()
        
        return {
            "status": status,
            "available": status.get("available", False)
        }
    
    except Exception as e:
        return {
            "status": "error",
            "available": False,
            "error": str(e)
        } 