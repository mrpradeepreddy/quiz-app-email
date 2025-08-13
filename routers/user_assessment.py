from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta, timezone # Added timezone
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
    AssessmentResult,
    StudentDashboardAssessment
)
from auth.jwt import get_current_user, require_student, require_admin

router = APIRouter(prefix="/user-assessments", tags=["User Assessments"])

# Add joinedload to your imports
from sqlalchemy.orm import joinedload

@router.get("/students/me/assessments", response_model=List[StudentDashboardAssessment])
def get_student_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all assessments assigned to or taken by the current student."""
    
    # Use .options(joinedload(...)) to pre-fetch the related assessment data
    # This turns N+1 queries into a single, efficient query.
    user_assessments = db.query(UserAssessment).options(
        joinedload(UserAssessment.assessment)
    ).filter(UserAssessment.user_id == current_user.id).all()

    # The rest of your code stays exactly the same, but now it's much faster
    # because 'ua.assessment.name' will not trigger a new database query.
    response_data = []
    for ua in user_assessments:
        response_data.append({
            "assessment_id": ua.assessment_id,
            "assessment_name": ua.assessment.name,
            "status": ua.status,
            "score": ua.score
        })
    return response_data


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

    # --- Part 1: Your existing validation is good ---
    
    # Use selectinload to pre-fetch related data efficiently
    user_assessment = db.query(UserAssessment).options(
        selectinload(UserAssessment.assessment).selectinload(Assessment.assessment_questions)
    ).filter(
        UserAssessment.id == user_assessment_id,
        UserAssessment.user_id == current_user.id
    ).first()

    if not user_assessment:
        raise HTTPException(status_code=404, detail="User assessment not found")

    if user_assessment.status == "Completed":
        raise HTTPException(status_code=400, detail="Assessment already completed")

    # Check for timeout using timezone-aware datetimes
    time_elapsed = datetime.now(timezone.utc) - user_assessment.start_time
    if time_elapsed.total_seconds() > user_assessment.assessment.duration * 60:
        raise HTTPException(status_code=400, detail="Assessment time has expired")

    # --- Part 2: Efficiently fetch all data in bulk (Replaces N+1 queries) ---
    
    # Get all question IDs for this assessment
    question_ids = [q.question_id for q in user_assessment.assessment.assessment_questions]
    
    # Get all relevant Question objects in one query
    questions_from_db = db.query(Question).filter(Question.id.in_(question_ids)).all()
    questions_map = {q.id: q for q in questions_from_db}

    # Get all correct choices for these questions in one query
    correct_choices_from_db = db.query(Choice).filter(
        Choice.question_id.in_(question_ids), 
        Choice.is_correct == True # Corrected from 'iss_correct'
    ).all()
    correct_choices_map = {c.question_id: c.id for c in correct_choices_from_db}

    # --- Part 3: Process answers with NO database calls inside the loop ---
    
    total_score = 0
    # Calculate total marks from the pre-fetched questions
    total_marks = sum(q.marks for q in questions_map.values())

    for answer_data in submission.answers:
        question_id = answer_data.question_id
        selected_choice_id = answer_data.selected_choice_id
        
        # Look up the correct choice ID from our pre-fetched map
        correct_choice_id = correct_choices_map.get(question_id)
        is_correct = (selected_choice_id is not None and selected_choice_id == correct_choice_id)
        
        if is_correct:
            # Look up the question's marks from our pre-fetched map
            total_score += questions_map[question_id].marks

        # Create the UserAnswer object to be saved
        user_answer = UserAnswer(
            user_assessment_id=user_assessment_id,
            question_id=answer_data.question_id,
            selected_choice_id=answer_data.selected_choice_id,
            is_correct=is_correct
        )
        db.add(user_answer)
        
    # --- Part 4: Finalize the assessment ---
    
    user_assessment.score = total_score
    user_assessment.end_time = datetime.now(timezone.utc) # Use timezone-aware datetime
    user_assessment.status = "Completed" # Update the status
    
    # Commit all changes (user answers and user assessment update) in one transaction
    db.commit()
    db.refresh(user_assessment)
    
    percentage = (total_score / total_marks * 100) if total_marks > 0 else 0
    
    return AssessmentResult(
        user_assessment_id=user_assessment_id,
        score=total_score,
        total_marks=total_marks,
        percentage=percentage,
        completed_at=user_assessment.end_time
    )


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
    if current_user.role != 'admin' and user_assessment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    answers = db.query(UserAnswer).filter(
        UserAnswer.user_assessment_id == user_assessment_id
    ).all()
    
    return answers



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
        UserAssessment.status == "Completed"
    ).count()
    
    # Efficiently calculate the average score directly in the database
    avg_score_result = db.query(func.avg(UserAssessment.score)).filter(
        UserAssessment.status == "Completed"
    ).scalar()

    return {
        "total_assessments_taken": total_assessments,
        "completed_assessments": completed_assessments,
        "average_score": avg_score_result or 0,
        "completion_rate": (completed_assessments / total_assessments * 100) if total_assessments > 0 else 0
    }







# @router.get("/my-assessments", response_model=List[UserAssessmentSchema])
# async def get_my_assessments(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get current user's assessments."""
#     user_assessments = db.query(UserAssessment).filter(
#         UserAssessment.user_id == current_user.id
#     ).all()
#     return user_assessments

# @router.get("/{user_assessment_id}", response_model=UserAssessmentSchema)
# async def get_user_assessment(
#     user_assessment_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get a specific user assessment."""
#     user_assessment = db.query(UserAssessment).filter(
#         UserAssessment.id == user_assessment_id,
#         UserAssessment.user_id == current_user.id
#     ).first()
    
#     if not user_assessment:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User assessment not found"
#         )
    
#     return user_assessment





# @router.get("/assessment/{assessment_id}/results", response_model=List[UserAssessmentSchema])
# async def get_assessment_results(
#     assessment_id: int,
#     current_user: User = Depends(require_admin),
#     db: Session = Depends(get_db)
# ):
#     """Get all results for an assessment (admin only)."""
#     user_assessments = db.query(UserAssessment).filter(
#         UserAssessment.assessment_id == assessment_id
#     ).all()
    
#     return user_assessments




# @router.delete("/{user_assessment_id}")
# async def delete_user_assessment(
#     user_assessment_id: int,
#     current_user: User = Depends(require_admin),
#     db: Session = Depends(get_db)
# ):
#     """Delete a user assessment (admin only)."""
#     user_assessment = db.query(UserAssessment).filter(
#         UserAssessment.id == user_assessment_id
#     ).first()
    
#     if not user_assessment:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User assessment not found"
#         )
    
#     db.delete(user_assessment)
#     db.commit()
    
#     return {"message": "User assessment deleted successfully"} 