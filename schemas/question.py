from pydantic import BaseModel
from typing import List,Optional
from datetime import datetime

class ChoiceBase(BaseModel):
    choice_text:str
    iss_correct:bool

class ChoiceCreate(ChoiceBase):
    pass

class Choice(ChoiceBase):
    id: int
    question_id: int

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question_text:str
    topic:Optional[str]=None
    level:Optional[str]=None

class QuestionCreate(QuestionBase):
    choices: List[ChoiceCreate]


# class QuestionUpdate(BaseModel):
#     question_text: Optional[str] = None
#     topic: Optional[str] = None
#     level: Optional[str] = None


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    topic: Optional[str] = None
    level: Optional[str] = None

    class Config:
        from_attributes = True

class Question(QuestionBase):
    id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    choices: List[Choice] = []

    class Config:
        from_attributes = True

class QuestionBulkCreate(BaseModel):
    questions: List[QuestionCreate]