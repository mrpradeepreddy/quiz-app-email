from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
from typing import Optional

from database.connection import engine, Base
from routers import auth, assessment, question, user_assessment, ai
from config.settings import settings

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Quiz Application...")
    yield
    # Shutdown
    print("Shutting down Quiz Application...")

app = FastAPI(
    title=settings.APP_NAME,
    description="A comprehensive quiz application with role-based authentication",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware, # The type of bouncer you're hiring.

    # This is the "Guest List".
    allow_origins=["*"],

    # "Can guests show special passes (like cookies)?"
    allow_credentials=True,

    # "What are guests allowed to DO inside?"
    allow_methods=["*"],

    # "What are guests allowed to BRING with them?"
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(assessment.router, prefix="/api/v1")
app.include_router(question.router, prefix="/api/v1")
app.include_router(user_assessment.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Quiz Application API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }

@app.get("/api/v1/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "Quiz Application with Role-Based Authentication",
        "features": [
            "JWT Authentication",
            "Role-based Access Control (Student/Admin)",
            "Assessment Management",
            "Question Management",
            "AI-powered Question Generation",
            "Assessment Taking and Scoring"
        ],
        "endpoints": {
            "authentication": "/api/v1/auth",
            "assessments": "/api/v1/assessments",
            "questions": "/api/v1/questions",
            "user_assessments": "/api/v1/user-assessments",
            "ai_services": "/api/v1/ai"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    ) 