import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.models_rd_station import (
    RDToken, 
    RDEmailAnalytics, 
    RDConversionAnalytics,
    RDSegmentation,
    RDLandingPage,
    RDWorkflow
)
from core.db import get_session, engine

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


def _cache_set(access_token: str, expires_in: Optional[int] = None, refresh_token: Optional[str] = None):
    token = _split_bearer(access_token)
    if not token:
        raise HTTPException(status_code=500, detail="access_token inválido")
    ttl = int(expires_in or 0)
    expires_at_ts = int(time.time()) + max(ttl - 30, 0) if ttl else int(time.time()) + 3600
    
    # Update memory cache
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = expires_at_ts

    # Persist to database
    db: Session = get_session()
    try:
        expires_at_dt = datetime.now() + timedelta(seconds=ttl if ttl else 3600)
        rd_token = db.query(RDToken).filter(RDToken.id == "current").first()
        if not rd_token:
            rd_token = RDToken(id="current")
            db.add(rd_token)
        
        rd_token.access_token = token
        rd_token.refresh_token = refresh_token
        rd_token.expires_at = expires_at_dt
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao salvar token RD no banco: {e}")
    finally:
        db.close()


def get_access_token() -> str:
    # 1. Check memory cache
    token = _token_cache.get("access_token")
    expires_at = int(_token_cache.get("expires_at") or 0)
    if token and int(time.time()) < expires_at:
        return str(token)
    
    # 2. Check database
    db: Session = get_session()
    try:
        rd_token = db.query(RDToken).filter(RDToken.id == "current").first()
        if rd_token:
            # Ensure comparison is done with naive datetimes if necessary, 
            # or handle aware datetimes consistently.
            # Usually, database datetimes without timezone are naive.
            expires_at = rd_token.expires_at
            if expires_at.tzinfo is not None:
                now = datetime.now(expires_at.tzinfo)
            else:
                now = datetime.now()
                
            if expires_at > now:
                # Update memory cache and return
                _token_cache["access_token"] = rd_token.access_token
                _token_cache["expires_at"] = int(rd_token.expires_at.timestamp())
                return rd_token.access_token
    finally:
        db.close()

    raise HTTPException(status_code=401, detail="RD Station não autenticado. Faça o OAuth em /rd/auth.")


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
    _cache_set(access_token, data.get("expires_in"), data.get("refresh_token"))
    return data


def oauth_callback(code: str, redirect_uri: str) -> Dict[str, Any]:
    return exchange_code_for_access_token(code=code, redirect_uri=redirect_uri)


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_access_token()}", "Content-Type": "application/json"}


def get_email_analytics(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Busca estatísticas de e-mail marketing (aberturas, cliques, envios).
    Corresponde aos dados das Imagens 1 e 3.
    """
    token = get_access_token()
    url = f"{RD_API_BASE}/analytics/emails"
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    params = {"start_date": start_date, "end_date": end_date}
    res = requests.get(url, headers=headers, params=params, timeout=30)
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.json())
    
    data = res.json()
    
    # Persistir dados no banco
    db: Session = get_session()
    try:
        emails = data.get("emails", [])
        for item in emails:
            # Upsert
            email_record = db.query(RDEmailAnalytics).filter(RDEmailAnalytics.campaign_id == item["campaign_id"]).first()
            if not email_record:
                email_record = RDEmailAnalytics(campaign_id=item["campaign_id"])
                db.add(email_record)
            
            email_record.campaign_name = item.get("campaign_name")
            email_record.send_at = datetime.fromisoformat(item.get("send_at").replace("Z", "+00:00"))
            email_record.email_dropped_count = item.get("email_dropped_count")
            email_record.email_delivered_count = item.get("email_delivered_count")
            email_record.email_bounced_count = item.get("email_bounced_count")
            email_record.email_opened_count = item.get("email_opened_count")
            email_record.email_clicked_count = item.get("email_clicked_count")
            email_record.email_unsubscribed_count = item.get("email_unsubscribed_count")
            email_record.email_spam_reported_count = item.get("email_spam_reported_count")
            email_record.email_delivered_rate = item.get("email_delivered_rate")
            email_record.email_opened_rate = item.get("email_opened_rate")
            email_record.email_clicked_rate = item.get("email_clicked_rate")
            email_record.email_spam_reported_rate = item.get("email_spam_reported_rate")
            email_record.contacts_count = item.get("contacts_count")
            
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao persistir analytics de e-mail: {e}")
    finally:
        db.close()
        
    return data


def get_conversions_analytics(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Busca estatísticas de conversões/leads.
    Corresponde aos dados da Imagem 2.
    """
    token = get_access_token()
    url = f"{RD_API_BASE}/analytics/conversions"
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    params = {"start_date": start_date, "end_date": end_date}
    res = requests.get(url, headers=headers, params=params, timeout=30)
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.json())
    
    data = res.json()
    
    # Persistir dados no banco
    db: Session = get_session()
    try:
        conversions = data.get("conversions", [])
        for item in conversions:
            # Upsert
            conv_record = db.query(RDConversionAnalytics).filter(RDConversionAnalytics.asset_id == item["asset_id"]).first()
            if not conv_record:
                conv_record = RDConversionAnalytics(asset_id=item["asset_id"])
                db.add(conv_record)
            
            conv_record.asset_identifier = item.get("asset_identifier")
            conv_record.asset_created_at = datetime.fromisoformat(item.get("asset_created_at").replace("Z", "+00:00"))
            conv_record.asset_updated_at = datetime.fromisoformat(item.get("asset_updated_at").replace("Z", "+00:00"))
            conv_record.assets_type = item.get("assets_type")
            conv_record.conversion_count = item.get("conversion_count")
            conv_record.visits_count = int(item.get("visits_count") or 0)
            conv_record.conversion_rate = item.get("conversion_rate")
            
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao persistir analytics de conversão: {e}")
    finally:
        db.close()

    return data


def get_segmentations() -> Dict[str, Any]:
    """
    Lista todas as segmentações de contatos.
    """
    token = get_access_token()
    url = f"{RD_API_BASE}/segmentations"
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    res = requests.get(url, headers=headers, timeout=30)
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.json())
    
    data = res.json()
    
    # Persistir no banco
    db: Session = get_session()
    try:
        segmentations = data.get("segmentations", [])
        for item in segmentations:
            seg_record = db.query(RDSegmentation).filter(RDSegmentation.id == item["id"]).first()
            if not seg_record:
                seg_record = RDSegmentation(id=item["id"])
                db.add(seg_record)
            
            seg_record.name = item.get("name")
            seg_record.standard = item.get("standard")
            seg_record.process_status = item.get("process_status")
            seg_record.created_at = datetime.fromisoformat(item.get("created_at").replace("Z", "+00:00"))
            seg_record.updated_at = datetime.fromisoformat(item.get("updated_at").replace("Z", "+00:00"))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao persistir segmentações: {e}")
    finally:
        db.close()
        
    return data


def get_landing_pages() -> Any:
    """
    Lista as Landing Pages ativas.
    """
    token = get_access_token()
    url = f"{RD_API_BASE}/landing_pages"
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    res = requests.get(url, headers=headers, timeout=30)
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.json())
    
    data = res.json()
    
    # Persistir no banco
    db: Session = get_session()
    try:
        # A API de Landing Pages retorna diretamente uma lista de objetos, 
        # e não um dicionário com a chave "landing_pages".
        lps = data if isinstance(data, list) else data.get("landing_pages", [])
        
        for item in lps:
            lp_record = db.query(RDLandingPage).filter(RDLandingPage.id == item["id"]).first()
            if not lp_record:
                lp_record = RDLandingPage(id=item["id"])
                db.add(lp_record)
            
            lp_record.title = item.get("title")
            lp_record.conversion_identifier = item.get("conversion_identifier")
            lp_record.status = item.get("status")
            lp_record.has_active_experiment = item.get("has_active_experiment")
            lp_record.had_experiment = item.get("had_experiment")
            lp_record.created_at = datetime.fromisoformat(item.get("created_at").replace("Z", "+00:00"))
            lp_record.updated_at = datetime.fromisoformat(item.get("updated_at").replace("Z", "+00:00"))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao persistir landing pages: {e}")
    finally:
        db.close()
        
    return data


def get_workflows() -> Dict[str, Any]:
    """
    Lista os fluxos de automação.
    """
    token = get_access_token()
    url = f"{RD_API_BASE}/workflows"
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    res = requests.get(url, headers=headers, timeout=30)
    if res.status_code >= 400:
        raise HTTPException(status_code=res.status_code, detail=res.json())
    
    data = res.json()
    
    # Persistir no banco
    db: Session = get_session()
    try:
        workflows = data.get("workflows", [])
        for item in workflows:
            wf_record = db.query(RDWorkflow).filter(RDWorkflow.id == item["id"]).first()
            if not wf_record:
                wf_record = RDWorkflow(id=item["id"])
                db.add(wf_record)
            
            wf_record.name = item.get("name")
            wf_record.user_email_created = item.get("user_email_created")
            wf_record.user_email_updated = item.get("user_email_updated")
            wf_record.status = item.get("configurations", {}).get("status")
            wf_record.created_at = datetime.fromisoformat(item.get("created_at").replace("Z", "+00:00"))
            wf_record.updated_at = datetime.fromisoformat(item.get("updated_at").replace("Z", "+00:00"))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao persistir workflows: {e}")
    finally:
        db.close()
        
    return data

