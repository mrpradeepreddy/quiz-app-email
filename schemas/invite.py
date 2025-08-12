# In file: schemas/invite.py

from pydantic import BaseModel, EmailStr
from typing import List

class InviteCreate(BaseModel):
    emails: List[EmailStr]
    assessment_id:int