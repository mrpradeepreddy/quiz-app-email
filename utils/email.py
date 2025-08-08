# In file: utils/email.py

import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from models.user import User # Import your SQLAlchemy User model

load_dotenv()

# --- Connection Configuration ---
# This is shared by all email functions in this file.
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False
)

# --- FUNCTION 1: For Welcoming New Users ---
async def send_welcome_email(email: EmailStr, username: str):
    """
    Sends a standard welcome email to any newly registered user.
    """
    html_content = f"""
    <html>
        <body>
            <h2>Welcome, {username}!</h2>
            <p>Thank you for registering for our amazing quiz app.</p>
            <p>You can now log in and get started. Good luck!</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Welcome to the FastAPI Quiz App! 🎉",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

# --- FUNCTION 2: For Recruiter Invitations ---
async def send_invite_email(recipient_email: str, recruiter: User, invitation_link: str):
    """
    Sends a personalized quiz invite with a unique link.
    """

    # UPDATED: The HTML content now includes the invitation_link
    html_content = f"""
    <html>
        <body>
            <h3>Hi there,</h3>
            <p>
                {recruiter.name} has invited you to take a quiz on our platform.
            </p>
            <p>
                Please click the link below to begin:
                <br>
                <a href="{invitation_link}">{invitation_link}</a>
            </p>
            <p>Good luck!</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject=f"Quiz Invitation from {recruiter.name}",
        recipients=[recipient_email],
        body=html_content,
        subtype="html",
        headers={"Reply-To": recruiter.email},
        sender=(f"{recruiter.name} (via QuizApp)", conf.MAIL_FROM)
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"--- Email successfully sent to {recipient_email} ---")
    except Exception as e:
        print(f"!!! FAILED TO SEND EMAIL TO {recipient_email} !!!")
        print(f"ERROR: {e}")