from pydantic import BaseModel,EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name:str
    role:str
    username:str
    email:EmailStr

class UserCreate(UserBase):
    password:str

class UserUpdate(BaseModel):
    name:Optional[str]=None
    email:Optional[EmailStr]=None
    role:Optional[str]=None
    username:Optional[str]=None
    password:Optional[str]=None

class User(UserBase):
    id:int 
    created_at:datetime
    updated_at:Optional[datetime]=None

    class Config:
        from_attribute=True

class UserLogin(BaseModel):
    email:EmailStr
    username:str
    password:str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class TokenData(BaseModel):
    username:Optional[str]=None
    id:Optional[int]=None
    role:Optional[str]=None