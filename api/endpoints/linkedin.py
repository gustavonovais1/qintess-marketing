from fastapi import APIRouter, Query
from services.linkedin import start_linkedin_bot
from fastapi import Depends
from core.auth import get_current_user_oauth
from models.models_user import User

router = APIRouter()

@router.post("/start")
def linkedin_start(segments: str = Query("updates,visitors,followers,competitors"), user: User = Depends(get_current_user_oauth)):
    return start_linkedin_bot(segments=segments)
