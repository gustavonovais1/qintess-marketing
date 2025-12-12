from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Optional
from core.db import Base, engine, get_session
from models.models_user import User
from core.auth import hash_password, verify_password, create_token, get_current_user_oauth
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.on_event("startup")
def _ensure_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

@router.post("/register")
def register(name: str = Body(...), email: str = Body(...), password: str = Body(...), role: str = Body("user")):
    s = get_session()
    try:
        existing = s.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=400, detail={"error":"email já cadastrado"})
        ph, salt = hash_password(password)
        u = User(name=name, email=email, password_hash=ph, password_salt=salt, role=role)
        s.add(u)
        s.commit()
        s.refresh(u)
        return {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
    finally:
        s.close()

@router.post("/login")
def login(email: str = Body(...), password: str = Body(...)):
    s = get_session()
    try:
        u: Optional[User] = s.query(User).filter(User.email == email).first()
        if not u:
            raise HTTPException(status_code=401, detail={"error":"credenciais inválidas"})
        if not verify_password(password, u.password_hash, u.password_salt):
            raise HTTPException(status_code=401, detail={"error":"credenciais inválidas"})
        token = create_token(u.id, expires_in=3600 * 12)
        return {"access_token": token, "token_type": "bearer"}
    finally:
        s.close()

@router.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends()):
    s = get_session()
    try:
        u: Optional[User] = s.query(User).filter(User.email == form_data.username).first()
        if not u:
            raise HTTPException(status_code=401, detail={"error":"credenciais inválidas"})
        if not verify_password(form_data.password, u.password_hash, u.password_salt):
            raise HTTPException(status_code=401, detail={"error":"credenciais inválidas"})
        token = create_token(u.id, expires_in=3600 * 12)
        return {"access_token": token, "token_type": "bearer"}
    finally:
        s.close()
@router.get("/me")
def me(user: User = Depends(get_current_user_oauth)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

@router.get("/")
def list_users(user: User = Depends(get_current_user_oauth)):
    if (user.role or "").lower() != "admin":
        raise HTTPException(status_code=403, detail={"error":"forbidden"})
    s = get_session()
    try:
        out = []
        for u in s.query(User).all():
            out.append({"id": u.id, "name": u.name, "email": u.email, "role": u.role})
        return {"users": out}
    finally:
        s.close()
