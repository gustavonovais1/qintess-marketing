from fastapi import APIRouter, Query
from services import start_linkedin_bot

router = APIRouter()

@router.post("/start")
def linkedin_start(segments: str = Query("updates,visitors,followers,competitors")):
    return start_linkedin_bot(segments=segments)