from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from models.user import User
from schemas.user import UserCreate, UserUpdate
from auth.jwt import get_password_hash


class UserService:
    @staticmethod
    def get_user_by_id(db:Session,user_id:int)->Optional[User]:
        return db.query(User).filter(User.id==user_id).first()
    
    @staticmethod
    def get_user_by_username(db:Session,Username:str)->Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_users(db:Session,skip:int=0,limit:int=100)->List[User]:
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_user(db:Session,user:UserCreate):
        hashed_password=get_password_hash(user.password)
        db_user=User(
            name=user.name,
            role=user.role,
            username=user.username,
            password_hash=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_user(db:Session,user_id:int,user_update:UserUpdate)->Optional[User]:
            db_user=UserService.get_user_by_id(db,user_id)
            if not db_user:
                 return None
            update_data=user_update.dict(exclude_unset=True)
            if "password" in update_data:
                 update_data["password_hash"]=get_password_hash(update_data.pop("password"))
            
            for field,value in update_data.items():
                 setattr(db_user,field,value)
            
            db.commit()
            db.refresh(db_user)
            return db_user
    
    @staticmethod
    def delete_user(db:Session,user_id:int)->bool:
         db_user=UserService.get_user_by_id(db,user_id)
         if not db_user:
              return False
         db.delete()
         db.commit()
         return True
    
    @staticmethod
    def check_username_exists(db:Session,username:str,exclude_id:Optional[int]=None):
        query=db.query(User).filter(User.username==username)
        if exclude_id:
            query=query.filter(User.id!=exclude_id)
        return query.first() is not None