from fastapi import APIRouter, Body, Depends, Query

from core.auth import get_current_user_oauth
from models.models_user import User
from services.rd_station import get_contact_fields, oauth_callback, send_event

router = APIRouter()
oauth_router = APIRouter()


@router.get("/oauth/callback")
def rd_oauth_callback(code: str = Query(...), redirect_uri: str = Query("http://localhost:8000/oauth/callback")):
    return oauth_callback(code=code, redirect_uri=redirect_uri)


@oauth_router.get("/oauth/callback")
def oauth_callback_root(code: str = Query(...), redirect_uri: str = Query("http://localhost:8000/oauth/callback")):
    return oauth_callback(code=code, redirect_uri=redirect_uri)


@router.post("/events")
def rd_events(payload: dict = Body(...), user: User = Depends(get_current_user_oauth)):
    return send_event(payload=payload)


@router.get("/contacts/fields")
def rd_contacts_fields(user: User = Depends(get_current_user_oauth)):
    return get_contact_fields()

