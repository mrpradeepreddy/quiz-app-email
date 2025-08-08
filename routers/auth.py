from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from database.connection import get_db
from models.user import User
from schemas.user import UserCreate, UserLogin, Token, User as UserSchema
from auth.jwt import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_user,
    require_admin,
    verify_password
)
from config.settings import settings
from utils.email import send_invite_email,send_welcome_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login endpoint for users."""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Return the role for the token
    primary_role = user.role
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": primary_role,
        "username": user.username
    }

@router.post("/register/admin", response_model=UserSchema)
async def register(user_data: UserCreate,background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Register a new user (admin only)."""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # IMPORTANT: Also check if the email is already in use
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    background_tasks.add_task(send_welcome_email,db_user.email,db_user.username)
    
    return db_user

@router.post("/register/student", response_model=UserSchema)
async def register_student(user_data: UserCreate,background_tasks:BackgroundTasks, db: Session = Depends(get_db)):
    """Register a new student (public endpoint)."""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # IMPORTANT: Also check if the email is already in use
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new student (force role to Student)
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        name=user_data.name,
        # IMPORTANT: Add the email field from the request data
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        role="Student"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # NEW: Add the email task to the background
    background_tasks.add_task(send_welcome_email, db_user.email, db_user.username)
    
    return db_user

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username, "user_id": current_user.id, "role": current_user.role},
        expires_delta=access_token_expires
    )
    
    primary_role = current_user.role
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": primary_role,
        "username": current_user.username
    }

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    from auth.jwt import verify_password, get_password_hash
    
    # Verify old password
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.get("/debug-role")
async def debug_role(current_user: User = Depends(get_current_user)):
    """Debug endpoint to check current user's role."""
    return {
        "username": current_user.username,
        "role": current_user.role,
        "role_type": type(current_user.role).__name__,
        "is_admin": current_user.role == "Admin"
    }

@router.get("/users", response_model=list[UserSchema])
async def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)."""
    users = db.query(User).all()
    return users 