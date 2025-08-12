from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from utils.email import send_invite_email
from database.connection import get_db
from models.user import User
from models.assessment import Assessment
from models.assessment_question import AssessmentQuestion
from models.question import Question
from schemas.assessment import (
    AssessmentCreate, 
    AssessmentUpdate, 
    Assessment as AssessmentSchema,
    AssessmentWithQuestions,
    AssessmentForDashboard
)
from models.user_assessment import UserAssessment, AssessmentStatus
from auth.jwt import get_current_user, require_admin, require_student
from schemas.invite import InviteCreate

router = APIRouter(prefix="/assessments", tags=["Assessments"])

@router.post("/create", response_model=AssessmentSchema,status_code=status.HTTP_201_CREATED)
def create_assessment(
    assessment_data: AssessmentCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new assessment (admin only)."""
    # Verify all questions exist
    for question_id in assessment_data.question_ids:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with id {question_id} not found"
            )
    
    # Create assessment
    db_assessment = Assessment(
        name=assessment_data.name,
        duration=assessment_data.duration,
        created_by_user_id=current_user.id
    )
    
    db.add(db_assessment)
    db.flush()
    db.refresh(db_assessment)
    
    # Add questions to assessment
    for question_id in assessment_data.question_ids:
        assessment_question = AssessmentQuestion(
            assessment_id=db_assessment.id,
            question_id=question_id
        )
        db.add(assessment_question)
    
    db.commit()
    return db_assessment

@router.get("/", response_model=List[AssessmentForDashboard])
def get_assessments(  # Removed async, as SQLAlchemy's default API is synchronous
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assessments (accessible by all authenticated users)."""
    
    # 1. Build the base query to get assessments and question counts together
    query = db.query(
        Assessment,
        func.count(AssessmentQuestion.question_id).label("total_questions")
    ).outerjoin(
        AssessmentQuestion, Assessment.id == AssessmentQuestion.assessment_id
    ).group_by(
        Assessment.id
    )

    # 2. Apply your role-based filtering to this more efficient query
    if current_user.role != 'admin':
        query = query.filter(Assessment.status == "published")

    # 3. Execute the single, powerful query
    results = query.all()

    # 4. Format the response. This loop makes NO new database calls.
    response_data = []
    for assessment, question_count in results:
        response_data.append({
            "id": assessment.id,
            "name": assessment.name,
            "duration": assessment.duration,
            "description": assessment.description,
            "status": assessment.status,
            "total_questions": question_count
        })

    return response_data

@router.get("/{assessment_id}", response_model=AssessmentWithQuestions)
async def get_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific assessment with question details."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Get question count and total marks
    questions = db.query(Question).join(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment_id
    ).all()
    
    total_questions = len(questions)
    total_marks = sum(question.marks for question in questions)
    
    return {
        **assessment.__dict__,
        "total_questions": total_questions,
        "total_marks": total_marks
    }

@router.post("/{assessment_id}/invite")
async def invite_students_to_assessment(
    assessment_id: int,
    invite_data: InviteCreate, # The Pydantic schema with a list of emails
    background_tasks:BackgroundTasks,
    db: Session = Depends(get_db),
    current_recruiter: User = Depends(get_current_user)):
    """
    Allows a logged-in recruiter to invite a list of students to a specific assessment.
    """
    invitations_to_email = []
    for email in invite_data.emails:
        # Create a new record using your hybrid model
        new_assessment_record = UserAssessment(
            student_email=email,
            recruiter_id=current_recruiter.id,
            assessment_id=assessment_id,
            status=AssessmentStatus.INVITED,
            # user_id is automatically NULL here
        )
        db.add(new_assessment_record)
        invitations_to_email.append(new_assessment_record)

    db.commit()
    
    for record in invitations_to_email:
        db.refresh(record) # Get the auto-generated unique_token
        invitation_link = f"https://your-frontend-app.com/take-quiz?token={record.unique_token}"
        
        background_tasks.add_task(
            send_invite_email,
            recipient_email=record.student_email,
            recruiter=current_recruiter,
            invitation_link=invitation_link
        )

    return {"message": f"Invitations are being sent to {len(invite_data.emails)} student(s)."}
    

@router.put("/{assessment_id}", response_model=AssessmentSchema)
async def update_assessment(
    assessment_id: int,
    assessment_data: AssessmentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update an assessment (admin only)."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Update fields
    if assessment_data.name is not None:
        assessment.name = assessment_data.name
    if assessment_data.duration is not None:
        assessment.duration = assessment_data.duration
    
    db.commit()
    db.refresh(assessment)
    return assessment

@router.delete("/{assessment_id}")
async def delete_assessment(
    assessment_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete an assessment (admin only)."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    db.delete(assessment)
    db.commit()
    return {"message": "Assessment deleted successfully"}

@router.post("/{assessment_id}/questions")
async def add_questions_to_assessment(
    assessment_id: int,
    question_ids: List[int],
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Add questions to an assessment (admin only)."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Verify all questions exist
    for question_id in question_ids:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with id {question_id} not found"
            )
        
        # Check if question is already in assessment
        existing = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.assessment_id == assessment_id,
            AssessmentQuestion.question_id == question_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {question_id} is already in this assessment"
            )
    
    # Add questions
    for question_id in question_ids:
        assessment_question = AssessmentQuestion(
            assessment_id=assessment_id,
            question_id=question_id
        )
        db.add(assessment_question)
    
    db.commit()
    return {"message": f"Added {len(question_ids)} questions to assessment"}

@router.delete("/{assessment_id}/questions/{question_id}")
async def remove_question_from_assessment(
    assessment_id: int,
    question_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Remove a question from an assessment (admin only)."""
    assessment_question = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment_id,
        AssessmentQuestion.question_id == question_id
    ).first()
    
    if not assessment_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in this assessment"
        )
    
    db.delete(assessment_question)
    db.commit()
    return {"message": "Question removed from assessment"}

@router.get("/{assessment_id}/questions")
async def get_assessment_questions(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all questions in an assessment."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    questions = db.query(Question).join(AssessmentQuestion).filter(
        AssessmentQuestion.assessment_id == assessment_id
    ).all()
    
    return questions 