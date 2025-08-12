# In file: routers/invites.py
from fastapi import APIRouter, Depends, BackgroundTasks
from schemas.invite import InviteCreate # Make sure to import your schema
from models.user import User
from auth.jwt import get_current_user
from utils.email import send_invite_email

# Define your frontend URL (replace with your actual domain later)
FRONTEND_URL = "http://localhost:8501" 

router = APIRouter(prefix="/invites", tags=["Invitations"])

@router.post("/send")
async def send_quiz_invite(
    payload: InviteCreate,
    background_tasks: BackgroundTasks,
    current_recruiter: User = Depends(get_current_user)
):
    for student_email in payload.emails:
        # Generate a unique invitation link for each student and assessment
        # A simple link can include the assessment ID and email.
        # For better security, you would generate and store a unique token here.
        invitation_link = f"{FRONTEND_URL}/?page=take_assessment&id={payload.assessment_id}"
        
        background_tasks.add_task(
            send_invite_email,
            recipient_email=student_email,
            recruiter=current_recruiter,
            invitation_link=invitation_link # Pass the generated link
        )

    return {"message": f"Invitations for assessment sent to {len(payload.emails)} student(s)."}