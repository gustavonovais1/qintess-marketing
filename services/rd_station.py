import os
import time
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

RD_TOKEN_URL = "https://api.rd.services/auth/token"
RD_API_BASE = "https://api.rd.services/platform"

_token_cache: Dict[str, Any] = {"access_token": None, "expires_at": 0}


def _env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise HTTPException(status_code=500, detail=f"{name} ausente no ambiente")
    return v


def _split_bearer(token: str) -> str:
    t = (token or "").strip()
    if t.lower().startswith("bearer "):
        return t[7:].strip()
    return t


def _cache_set(access_token: str, expires_in: Optional[int] = None):
    token = _split_bearer(access_token)
    if not token:
        raise HTTPException(status_code=500, detail="access_token inválido")
    ttl = int(expires_in or 0)
    expires_at = int(time.time()) + max(ttl - 30, 0) if ttl else int(time.time()) + 3600
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = expires_at


def get_access_token() -> str:
    token = _token_cache.get("access_token")
    expires_at = int(_token_cache.get("expires_at") or 0)
    if token and int(time.time()) < expires_at:
        return str(token)
    raise HTTPException(status_code=401, detail="RD Station não autenticado. Faça o OAuth em /oauth/callback.")


def exchange_code_for_access_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    client_id = _env("RD_ACCOUNT_ID")
    client_secret = _env("RD_CLIENT_SECRET")
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    try:
        res = requests.post(RD_TOKEN_URL, data=payload, timeout=30)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao chamar RD token endpoint: {e}")
    if res.status_code >= 400:
        try:
            detail = res.json()
        except Exception:
            detail = res.text
        raise HTTPException(status_code=res.status_code, detail=detail)
    try:
        data = res.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Resposta inválida do token endpoint")
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail=data)
    _cache_set(access_token, data.get("expires_in"))
    return data


def oauth_callback(code: str, redirect_uri: str) -> Dict[str, Any]:
    return exchange_code_for_access_token(code=code, redirect_uri=redirect_uri)


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_access_token()}", "Content-Type": "application/json"}


def send_event(payload: dict) -> Dict[str, Any]:
    try:
        res = requests.post(f"{RD_API_BASE}/events", json=payload, headers=_headers(), timeout=30)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao enviar evento ao RD Station: {e}")
    if res.status_code >= 400:
        try:
            detail = res.json()
        except Exception:
            detail = res.text
        raise HTTPException(status_code=res.status_code, detail=detail)
    try:
        return res.json()
    except Exception:
        return {"status_code": res.status_code, "text": res.text}


def get_contact_fields() -> Dict[str, Any]:
    try:
        res = requests.get(f"{RD_API_BASE}/contacts/fields", headers=_headers(), timeout=30)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao buscar campos de contato no RD Station: {e}")
    if res.status_code >= 400:
        try:
            detail = res.json()
        except Exception:
            detail = res.text
        raise HTTPException(status_code=res.status_code, detail=detail)
    try:
        return res.json()
    except Exception:
        return {"status_code": res.status_code, "text": res.text}

