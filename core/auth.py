import os
import hmac
import hashlib
import base64
import time
from typing import Optional
from fastapi import HTTPException, Header, Depends
from fastapi.security import OAuth2PasswordBearer
from core.db import get_session
from models.models_user import User
import jwt
from datetime import datetime, timedelta

def _secret() -> bytes:
    s = os.environ.get("AUTH_SECRET") or os.environ.get("SECRET_KEY") or "dev-secret"
    return s.encode("utf-8")

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return base64.b64encode(dk).decode("utf-8"), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    dk, _ = hash_password(password, salt)
    return hmac.compare_digest(dk, password_hash)

def create_token(user_id: int, expires_in: int = 3600) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": int(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=int(expires_in))).timestamp()),
    }
    return jwt.encode(payload, _secret(), algorithm=os.environ.get("JWT_ALG") or "HS256")

def verify_token(token: str) -> Optional[int]:
    try:
        data = jwt.decode(token, _secret(), algorithms=[os.environ.get("JWT_ALG") or "HS256"])
        sub = data.get("sub")
        return int(sub) if sub is not None else None
    except Exception:
        return None

def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"error":"missing bearer token"})
    token = authorization.split(" ", 1)[1]
    uid = verify_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail={"error":"invalid or expired token"})
    s = get_session()
    user = s.get(User, uid)
    s.close()
    if not user:
        raise HTTPException(status_code=401, detail={"error":"user not found"})
    return user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/token")

def get_current_user_oauth(token: str = Depends(oauth2_scheme)) -> User:
    uid = verify_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail={"error":"invalid or expired token"})
    s = get_session()
    user = s.get(User, uid)
    s.close()
    if not user:
        raise HTTPException(status_code=401, detail={"error":"user not found"})
    return user
