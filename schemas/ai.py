from pydantic import BaseModel
from typing import List
from enum import Enum

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionGenerationRequest(BaseModel):
    topic: str
    difficulty:DifficultyLevel=DifficultyLevel.MEDIUM
    count:int = 5

class GeneratedChoice(BaseModel):
    choice_text:str
    is_correct:bool

class GeneratedQuestion(BaseModel):
    question_text:str
    topic:str
    level:str
    choices:List[GeneratedChoice]

class QuestionGenerationResponse(BaseModel):
    question:List[GeneratedQuestion]