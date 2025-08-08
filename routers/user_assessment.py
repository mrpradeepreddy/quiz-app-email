from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database.connection import get_db
from models.user import User
from models.assessment import Assessment
from models.user_assessment import UserAssessment
from models.user_answer import UserAnswer
from models.question import Question
from models.choice import Choice
from models.assessment_question import AssessmentQuestion
from schemas.user_assessment import (
    UserAssessmentCreate,
    UserAssessment as UserAssessmentSchema,
    UserAnswerCreate,
    UserAnswer as UserAnswerSchema,
    AssessmentSubmission,
    AssessmentResult
)
from auth.jwt import get_current_user, require_student, require_admin

router = APIRouter(prefix="/user-assessments", tags=["User Assessments"])

@router.post("/start", response_model=UserAssessmentSchema)
async def start_assessment(
    assessment_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Start an assessment (student only)."""
    # Check if assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Check if user already has an active assessment
    active_assessment = db.query(UserAssessment).filter(
        UserAssessment.user_id == current_user.id,
        UserAssessment.assessment_id == assessment_id,
        UserAssessment.end_time.is_(None)
    ).first()
    
    if active_assessment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active assessment for this test"
        )
    
    # Create new user assessment
    user_assessment = UserAssessment(
        user_id=current_user.id,
        assessment_id=assessment_id,
        start_time=datetime.utcnow()
    )
    
    db.add(user_assessment)
    db.commit()
    db.refresh(user_assessment)
    
    return user_assessment

@router.post("/{user_assessment_id}/submit", response_model=AssessmentResult)
async def submit_assessment(
    user_assessment_id: int,
    submission: AssessmentSubmission,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Submit answers for an assessment (student only)."""
    # Get user assessment
    user_assessment = db.query(UserAssessment).filter(
        UserAssessment.id == user_assessment_id,
        UserAssessment.user_id == current_user.id
    ).first()
    
    if not user_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User assessment not found"
        )
    
    if user_assessment.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment already completed"
        )
    
    # Check if assessment time has expired
    assessment = db.query(Assessment).filter(Assessment.id == user_assessment.assessment_id).first()
    time_elapsed = datetime.utcnow() - user_assessment.start_time
    if time_elapsed.total_seconds() > assessment.duration * 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment time has expired"
        )
    
    # Get assessment questions
    assessment_questions = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == user_assessment.assessment_id
    ).all()
    
    question_ids = [aq.question_id for aq in assessment_questions]
    
    # Validate that all questions are answered
    submitted_question_ids = [answer.question_id for answer in submission.answers]
    if set(submitted_question_ids) != set(question_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All questions must be answered"
        )
    
    # Process answers and calculate score
    total_score = 0
    total_marks = 0
    
    for answer_data in submission.answers:
        # Get question and its marks
        question = db.query(Question).filter(Question.id == answer_data.question_id).first()
        if not question:
            continue
        
        total_marks += question.marks
        
        # Check if answer is correct
        is_correct = False
        if answer_data.selected_choice_id:
            selected_choice = db.query(Choice).filter(
                Choice.id == answer_data.selected_choice_id,
                Choice.question_id == answer_data.question_id
            ).first()
            
            if selected_choice and selected_choice.iss_correct:
                is_correct = True
                total_score += question.marks
        
        # Save user answer
        user_answer = UserAnswer(
            user_assessment_id=user_assessment_id,
            question_id=answer_data.question_id,
            selected_choice_id=answer_data.selected_choice_id,
            is_correct=is_correct
        )
        db.add(user_answer)
    
    # Update user assessment
    user_assessment.score = total_score
    user_assessment.end_time = datetime.utcnow()
    
    db.commit()
    db.refresh(user_assessment)
    
    # Calculate percentage
    percentage = (total_score / total_marks * 100) if total_marks > 0 else 0
    
    return AssessmentResult(
        user_assessment_id=user_assessment_id,
        score=total_score,
        total_marks=total_marks,
        percentage=percentage,
        completed_at=user_assessment.end_time
    )

@router.get("/my-assessments", response_model=List[UserAssessmentSchema])
async def get_my_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's assessments."""
    user_assessments = db.query(UserAssessment).filter(
        UserAssessment.user_id == current_user.id
    ).all()
    return user_assessments

@router.get("/{user_assessment_id}", response_model=UserAssessmentSchema)
async def get_user_assessment(
    user_assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user assessment."""
    user_assessment = db.query(UserAssessment).filter(
        UserAssessment.id == user_assessment_id,
        UserAssessment.user_id == current_user.id
    ).first()
    
    if not user_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User assessment not found"
        )
    
    return user_assessment

@router.get("/{user_assessment_id}/answers", response_model=List[UserAnswerSchema])
async def get_user_answers(
    user_assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get answers for a user assessment."""
    # Verify ownership or admin access
    user_assessment = db.query(UserAssessment).filter(
        UserAssessment.id == user_assessment_id
    ).first()
    
    if not user_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User assessment not found"
        )
    
    # Check if user is admin or the owner
    if "Admin" not in current_user.roles and user_assessment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    answers = db.query(UserAnswer).filter(
        UserAnswer.user_assessment_id == user_assessment_id
    ).all()
    
    return answers

@router.get("/assessment/{assessment_id}/results", response_model=List[UserAssessmentSchema])
async def get_assessment_results(
    assessment_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all results for an assessment (admin only)."""
    user_assessments = db.query(UserAssessment).filter(
        UserAssessment.assessment_id == assessment_id
    ).all()
    
    return user_assessments

@router.get("/statistics")
async def get_assessment_statistics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get assessment statistics (admin only)."""
    # Total assessments taken
    total_assessments = db.query(UserAssessment).count()
    
    # Completed assessments
    completed_assessments = db.query(UserAssessment).filter(
        UserAssessment.end_time.isnot(None)
    ).count()
    
    # Average score
    completed_with_scores = db.query(UserAssessment).filter(
        UserAssessment.end_time.isnot(None),
        UserAssessment.score.isnot(None)
    ).all()
    
    avg_score = 0
    if completed_with_scores:
        total_score = sum(ua.score for ua in completed_with_scores)
        avg_score = total_score / len(completed_with_scores)
    
    return {
        "total_assessments_taken": total_assessments,
        "completed_assessments": completed_assessments,
        "average_score": avg_score,
        "completion_rate": (completed_assessments / total_assessments * 100) if total_assessments > 0 else 0
    }

@router.delete("/{user_assessment_id}")
async def delete_user_assessment(
    user_assessment_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user assessment (admin only)."""
    user_assessment = db.query(UserAssessment).filter(
        UserAssessment.id == user_assessment_id
    ).first()
    
    if not user_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User assessment not found"
        )
    
    db.delete(user_assessment)
    db.commit()
    
    return {"message": "User assessment deleted successfully"} 