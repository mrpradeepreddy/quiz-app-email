from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL:str="postgresql://postgres:password@localhost:5432/quiz_app"


    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


    # AI Configuration
    GEMINI_API_KEY: Optional[str] = None
    
    # App Configuration
    APP_NAME: str = "Quiz Application"
    DEBUG: bool = True

     # --- Email Configuration (NEW) ---
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 


#DEBUG:bool=True
'''Error Handling: When an unhandled error occurs, the application will send a detailed error page back to the client. 
This page typically includes the full stack trace, the line of code where the error happened, and the values of local variables. 
This is a huge help for a developer.

Logging: The application will generate verbose logs, often at the DEBUG level. This can include messages about every request, 
database query, or internal function call.'''

#debug = False (Production Mode)
'''Error Handling: When an unhandled error occurs, the application will not send the detailed stack trace to the user. Instead, it will:
Return a generic status code, such as 500 Internal Server Error, to the user.
Serve a simple, non-technical error page (e.g., "An unexpected error occurred.").
The detailed error information (the stack trace) is not lost; it is written to a log file on the server. This is a crucial distinction. 
The error is logged for administrators to review, but it's hidden from the public to prevent information leakage.

Logging: The logging level is typically set higher (e.g., INFO or ERROR) to reduce noise. Only significant events are logged.'''