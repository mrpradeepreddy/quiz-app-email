from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AssessmentBase(BaseModel):
    name: str
    duration: int  # in minutes

class AssessmentCreate(AssessmentBase):
    question_ids: List[int]  # List of question IDs to include


class AssessmentUpdate(BaseModel):
    name: Optional[str] = None
    duration: Optional[int] = None

class Assessment(AssessmentBase):
    id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AssessmentWithQuestions(Assessment):
    total_questions: int
    total_marks: int 