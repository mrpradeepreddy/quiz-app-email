from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from models.assessment import Assessment
from models.assessment_question import AssessmentQuestion
from models.question import Question
from schemas.assessment import AssessmentCreate, AssessmentUpdate
from fastapi import HTTPException

class AssessmentService:
    @staticmethod
    def get_assessment_by_id(db: Session, assessment_id: int) -> Optional[Assessment]:
        return db.query(Assessment).filter(Assessment.id == assessment_id).first()
    
    @staticmethod
    def get_assessments(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        created_by_user_id: Optional[int] = None
    ) -> List[Assessment]:
        query = db.query(Assessment)
        
        if created_by_user_id:
            query = query.filter(Assessment.created_by_user_id == created_by_user_id)
        
        return query.offset(skip).limit(limit).all()
    

    @staticmethod
    def create_assessment(db: Session, assessment: AssessmentCreate, user_id: int) -> Assessment:
        # Create assessment
        db_assessment = Assessment(
            name=assessment.name,
            duration=assessment.duration,
            created_by_user_id=user_id
        )
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)
        
        # Add questions to assessment
        for question_id in assessment.question_ids:
            # Verify question exists
            question = db.query(Question).filter(Question.id == question_id).first()
            if not question:
                raise HTTPException(status_code=400, detail=f"Question with id {question_id} not found")
            
            # Add question to assessment with default marks
            assessment_question = AssessmentQuestion(
                assessment_id=db_assessment.id,
                question_id=question_id,
                marks=1  # Default marks per question
            )
            db.add(assessment_question)
        
        db.commit()
        db.refresh(db_assessment)
        return db_assessment
    

    @staticmethod
    def update_assessment(db: Session, assessment_id: int, assessment_update: AssessmentUpdate) -> Optional[Assessment]:
        db_assessment = AssessmentService.get_assessment_by_id(db, assessment_id)
        if not db_assessment:
            return None
        
        update_data = assessment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_assessment, field, value)
        
        db.commit()
        db.refresh(db_assessment)
        return db_assessment
    

    @staticmethod
    def delete_assessment(db: Session, assessment_id: int) -> bool:
        db_assessment = AssessmentService.get_assessment_by_id(db, assessment_id)
        if not db_assessment:
            return False
        
        db.delete(db_assessment)
        db.commit()
        return True
    
    @staticmethod
    def get_assessment_questions(db: Session, assessment_id: int) -> List[Question]:
        """Get all questions for an assessment"""
        return db.query(Question).join(AssessmentQuestion).filter(
            AssessmentQuestion.assessment_id == assessment_id
        ).all()
    
    #doubt
    @staticmethod
    def get_assessment_with_stats(db: Session, assessment_id: int) -> Optional[dict]:
        """Get assessment with question count and total marks"""
        assessment = AssessmentService.get_assessment_by_id(db, assessment_id)
        if not assessment:
            return None
        
        # Get question count and total marks
        stats = db.query(
            func.count(AssessmentQuestion.question_id).label('total_questions'),
            func.sum(AssessmentQuestion.marks).label('total_marks')
        ).filter(AssessmentQuestion.assessment_id == assessment_id).first()
        
        return {
            "assessment": assessment,
            "total_questions": stats.total_questions or 0,
            "total_marks": stats.total_marks or 0
        }
    
    @staticmethod
    def add_question_to_assessment(db: Session, assessment_id: int, question_id: int, marks: int = 1) -> bool:
        """Add a question to an assessment"""
        # Check if assessment exists
        assessment = AssessmentService.get_assessment_by_id(db, assessment_id)
        if not assessment:
            return False
        
        # Check if question exists
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False
        
        # Check if question is already in assessment
        existing = db.query(AssessmentQuestion).filter(
            and_(AssessmentQuestion.assessment_id == assessment_id, 
                 AssessmentQuestion.question_id == question_id)
        ).first()
        
        if existing:
            return False
        
        # Add question to assessment
        assessment_question = AssessmentQuestion(
            assessment_id=assessment_id,
            question_id=question_id,
            marks=marks
        )
        db.add(assessment_question)
        db.commit()
        return True
    
    @staticmethod
    def remove_question_from_assessment(db: Session, assessment_id: int, question_id: int) -> bool:
        """Remove a question from an assessment"""
        assessment_question = db.query(AssessmentQuestion).filter(
            and_(AssessmentQuestion.assessment_id == assessment_id, 
                 AssessmentQuestion.question_id == question_id)
        ).first()
        
        if not assessment_question:
            return False
        
        db.delete(assessment_question)
        db.commit()
        return True 