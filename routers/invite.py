# In file: routers/invites.py

from fastapi import APIRouter, Depends, BackgroundTasks
from auth.jwt import get_current_user
from models.user import User
from utils.email import send_invite_email

router = APIRouter(prefix="/invites", tags=["Invitations"])

@router.post("/send")
async def send_quiz_invite(
    student_email: str,
    background_tasks: BackgroundTasks,
    current_recruiter: User = Depends(get_current_user)
):
    background_tasks.add_task(
        send_invite_email,
        recipient_email=student_email,
        recruiter=current_recruiter
    )

    return {"message": f"Invitation sent to {student_email}."}