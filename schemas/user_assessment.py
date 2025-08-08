from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserAssessmentBase(BaseModel):
    assessment_id: int


class UserAssessmentCreate(UserAssessmentBase):
    pass

class UserAssessment(UserAssessmentBase):
    id: int
    user_id: int
    score: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserAnswerBase(BaseModel):
    question_id: int
    selected_choice_id: Optional[int] = None

class UserAnswerCreate(UserAnswerBase):
    pass

class UserAnswer(UserAnswerBase):
    user_assessment_id: int
    is_correct: Optional[bool] = None
    
    class Config:
        from_attributes = True

class AssessmentSubmission(BaseModel):
    answers: List[UserAnswerCreate]


class AssessmentResult(BaseModel):
    user_assessment_id: int
    score: int
    total_marks: int
    percentage: float
    completed_at: datetime 

