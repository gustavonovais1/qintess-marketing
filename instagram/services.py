import os
import requests
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from .db import get_session
from .models import InsightsProfile, InsightsPost, OAuthToken

def _active_token() -> str:
    s = get_session()
    obj = s.get(OAuthToken, "meta")
    s.close()
    if not obj:
        raise HTTPException(status_code=401, detail={"error":"token ausente"})
    now = datetime.now(timezone.utc)
    if obj.expires_at <= now:
        raise HTTPException(status_code=401, detail={"error":"token expirado"})
    return obj.access_token

def _graph_get(path: str, extra_params: dict):
    base = os.environ.get("META_GRAPH_BASE") or "https://graph.facebook.com/v24.0"
    token = _active_token()
    params = {"access_token": token}
    for k, v in (extra_params or {}).items():
        if v is not None:
            params[k] = v
    url = base.rstrip("/") + "/" + path.lstrip("/")
    r = requests.get(url, params=params, timeout=60)
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = {"error": r.text, "status": r.status_code}
        raise HTTPException(status_code=r.status_code, detail=detail)
    try:
        return r.json()
    except Exception:
        return {"raw": r.text}

def _env_ig_id() -> str:
    iid = os.environ.get("IG_ACCOUNT_ID")
    if not iid:
        raise HTTPException(status_code=500, detail="IG_ACCOUNT_ID ausente no ambiente")
    return iid

def _persist_monthly_insights(payload: dict, ig_account_id: int, year: int, month: int) -> tuple[bool, str | None]:
    try:
        data = payload.get("data") or []
        vals = {
            "reach": 0,
            "website_clicks": 0,
            "profile_views": 0,
            "accounts_engaged": 0,
            "total_interactions": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "saves": 0,
            "replies": 0,
            "follows_and_unfollows": 0,
            "profile_links_taps": 0,
            "views": 0,
            "reposts": 0,
            "content_views": 0,
        }
        for item in data:
            name = str(item.get("name") or "").strip()
            tv = item.get("total_value") or {}
            val = tv.get("value")
            if val is None:
                continue
            if name in vals:
                try:
                    vals[name] = int(val)
                except Exception:
                    try:
                        vals[name] = int(float(val))
                    except Exception:
                        pass
        s = get_session()
        obj = s.get(InsightsProfile, (int(ig_account_id), int(year), int(month)))
        if obj is None:
            obj = InsightsProfile(ig_account_id=int(ig_account_id), year=int(year), month=int(month))
        obj.reach = vals["reach"]
        obj.website_clicks = vals["website_clicks"]
        obj.profile_views = vals["profile_views"]
        obj.accounts_engaged = vals["accounts_engaged"]
        obj.total_interactions = vals["total_interactions"]
        obj.likes = vals["likes"]
        obj.comments = vals["comments"]
        obj.shares = vals["shares"]
        obj.saves = vals["saves"]
        obj.replies = vals["replies"]
        obj.follows_and_unfollows = vals["follows_and_unfollows"]
        obj.profile_links_taps = vals["profile_links_taps"]
        obj.views = vals["views"]
        obj.reposts = vals["reposts"]
        obj.content_views = vals["content_views"]
        s.add(obj)
        s.commit()
        s.close()
        return True, None
    except Exception as e:
        try:
            err = str(e)
        except Exception:
            err = "erro desconhecido"
        return False, err

def _persist_post_insights(media: dict, insights: dict) -> tuple[bool, str | None]:
    try:
        mid = str(media.get("id") or "").strip()
        mt = str(media.get("media_type") or "").strip()
        ts_raw = media.get("timestamp")
        dtv = None
        try:
            if isinstance(ts_raw, str) and ts_raw:
                try:
                    dtv = datetime.strptime(ts_raw, "%Y-%m-%dT%H:%M:%S%z")
                except Exception:
                    dtv = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except Exception:
            dtv = None
        cap = media.get("caption")
        pl = media.get("permalink")
        mu = media.get("media_url")
        vals = {
            "views": None,
            "reach": None,
            "saves": None,
            "likes": None,
            "comments": None,
            "shares": None,
            "total_interactions": None,
            "follows": None,
            "profile_visits": None,
            "profile_activity": None,
            "reposts": None,
            "ig_reels_video_view_total_time": None,
            "ig_reels_avg_watch_time": None,
            "reels_skip_rate": None,
            "facebook_views": None,
            "crossposted_views": None,
        }
        data = insights.get("data") if isinstance(insights, dict) else []
        for item in (data or []):
            name = str(item.get("name") or "").strip()
            val = None
            vs = item.get("values") or []
            if isinstance(vs, list) and vs:
                try:
                    val = vs[0].get("value")
                except Exception:
                    val = None
            if name == "saved":
                name = "saves"
            if name in vals:
                if name in ("ig_reels_avg_watch_time","reels_skip_rate"):
                    try:
                        vals[name] = float(val)
                    except Exception:
                        pass
                else:
                    try:
                        vals[name] = int(val)
                    except Exception:
                        try:
                            vals[name] = int(float(val))
                        except Exception:
                            pass
        s = get_session()
        obj = s.get(InsightsPost, mid)
        if obj is None:
            obj = InsightsPost(media_id=mid)
        obj.media_type = mt
        obj.timestamp = dtv
        obj.caption = cap
        obj.permalink = pl
        obj.media_url = mu
        obj.views = vals["views"]
        obj.reach = vals["reach"]
        obj.saves = vals["saves"]
        obj.likes = vals["likes"]
        obj.comments = vals["comments"]
        obj.shares = vals["shares"]
        obj.total_interactions = vals["total_interactions"]
        obj.follows = vals["follows"]
        obj.profile_visits = vals["profile_visits"]
        obj.profile_activity = vals["profile_activity"]
        obj.reposts = vals["reposts"]
        obj.ig_reels_video_view_total_time = vals["ig_reels_video_view_total_time"]
        obj.ig_reels_avg_watch_time = vals["ig_reels_avg_watch_time"]
        obj.reels_skip_rate = vals["reels_skip_rate"]
        obj.facebook_views = vals["facebook_views"]
        obj.crossposted_views = vals["crossposted_views"]
        s.add(obj)
        s.commit()
        s.close()
        return True, None
    except Exception as e:
        try:
            err = str(e)
        except Exception:
            err = "erro desconhecido"
        return False, err

def media_list(fields: str, limit: int, media_type: str | None, since: int | str | None, until: int | str | None):
    params = {"fields": fields, "limit": limit}
    res = _graph_get(f"{_env_ig_id()}/media", params)
    types = None
    if media_type:
        types = {t.strip().upper() for t in media_type.split(",") if t.strip()}
    def _parse_ts(v):
        if v is None:
            return None
        if isinstance(v, int):
            return v
        s = str(v).strip()
        try:
            dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            try:
                return int(s)
            except Exception:
                return None
    s_ts = _parse_ts(since)
    u_ts = _parse_ts(until)
    try:
        data = res.get("data") if isinstance(res, dict) else []
        out = []
        for item in (data or []):
            ok = True
            mt = str(item.get("media_type") or "").upper()
            if types and mt not in types:
                ok = False
            if ok and (s_ts or u_ts):
                ts_iso = item.get("timestamp")
                tsv = None
                try:
                    if isinstance(ts_iso, str) and ts_iso:
                        try:
                            dt = datetime.strptime(ts_iso, "%Y-%m-%dT%H:%M:%S%z")
                        except Exception:
                            dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
                        tsv = int(dt.timestamp())
                except Exception:
                    tsv = None
                if tsv is None:
                    ok = False
                if ok and s_ts is not None and tsv < s_ts:
                    ok = False
                if ok and u_ts is not None and tsv > u_ts:
                    ok = False
            if ok:
                out.append(item)
        if isinstance(res, dict):
            res["data"] = out
    except Exception:
        pass
    return res

def get_profile(fields: str):
    return _graph_get(f"{_env_ig_id()}", {"fields": fields})

def _validate_insights_params(metrics: list[str], period: str | None, timeframe: str | None, metric_type: str | None, breakdown: str | None):
    allowed_metrics = {
        "reach",
        "follower_count",
        "website_clicks",
        "profile_views",
        "online_followers",
        "accounts_engaged",
        "total_interactions",
        "likes",
        "comments",
        "shares",
        "saves",
        "replies",
        "engaged_audience_demographics",
        "reached_audience_demographics",
        "follower_demographics",
        "follows_and_unfollows",
        "profile_links_taps",
        "views",
        "threads_likes",
        "threads_replies",
        "reposts",
        "quotes",
        "threads_followers",
        "threads_follower_demographics",
        "content_views",
        "threads_views",
        "threads_clicks",
        "threads_reposts",
    }
    if any(m == "impressions" for m in metrics):
        raise HTTPException(status_code=400, detail={"error":"'impressions' está deprecada a partir da v22.0; use 'views'"})
    unknown = [m for m in metrics if m not in allowed_metrics]
    if unknown:
        raise HTTPException(status_code=400, detail={"error":"métricas inválidas","metrics":unknown})
    if metric_type and metric_type not in ("time_series","total_value"):
        raise HTTPException(status_code=400, detail={"error":"metric_type inválido; use 'time_series' ou 'total_value'"})
    if breakdown:
        allowed_breakdowns = {"contact_button_type","follow_type","media_product_type"}
        if breakdown not in allowed_breakdowns:
            raise HTTPException(status_code=400, detail={"error":"breakdown inválido","allowed":list(allowed_breakdowns)})
        if (metric_type or "") != "total_value":
            raise HTTPException(status_code=400, detail={"error":"breakdown requer metric_type=total_value"})
    ts = {
        "reach",
        "profile_views",
        "website_clicks",
        "follower_count",
        "content_views",
        "threads_views",
        "threads_clicks",
    }
    demo = {
        "engaged_audience_demographics",
        "reached_audience_demographics",
        "follower_demographics",
        "threads_follower_demographics",
    }
    totals = {
        "likes",
        "comments",
        "shares",
        "saves",
        "replies",
        "accounts_engaged",
        "total_interactions",
        "follows_and_unfollows",
        "profile_links_taps",
        "views",
        "reposts",
        "quotes",
        "threads_likes",
        "threads_replies",
        "threads_reposts",
    }
    if any(m in demo for m in metrics):
        if timeframe is None:
            raise HTTPException(status_code=400, detail={"error":"timeframe é obrigatório para métricas demográficas"})
        if period is not None:
            raise HTTPException(status_code=400, detail={"error":"period não deve ser usado com métricas demográficas"})
        if metric_type:
            raise HTTPException(status_code=400, detail={"error":"metric_type não é suportado para métricas demográficas"})
    if any(m == "online_followers" for m in metrics):
        if (period or "") != "lifetime":
            raise HTTPException(status_code=400, detail={"error":"online_followers requer period=lifetime"})
    if any(m == "follower_count" for m in metrics):
        if (period or "") != "day":
            raise HTTPException(status_code=400, detail={"error":"follower_count requer period=day"})
    if any(m in ts for m in metrics):
        if period is None:
            raise HTTPException(status_code=400, detail={"error":"period é obrigatório para métricas time-series"})
    if any(m in totals for m in metrics):
        if (metric_type or "") != "total_value":
            raise HTTPException(status_code=400, detail={"error":"métricas de engajamento agregado requerem metric_type=total_value"})
        if period is None:
            raise HTTPException(status_code=400, detail={"error":"period é obrigatório para metric_type=total_value"})

def get_insights_profile(metric: str, since: int | str | None, until: int | str | None):
    period = "day"
    metric_type = "total_value"
    mets = [m.strip() for m in (metric or "").split(",") if m.strip()]
    _validate_insights_params(mets, period, None, metric_type, None)
    if since is None and until is None:
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        since = int(start.timestamp())
        until = int(now.timestamp())
    def _parse_ts(v):
        if v is None:
            return None
        if isinstance(v, int):
            return v
        s = str(v).strip()
        try:
            dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            try:
                return int(s)
            except Exception:
                raise HTTPException(status_code=400, detail={"error":"since/until devem ser YYYY-MM-DD ou timestamp unix"})
    since = _parse_ts(since)
    until = _parse_ts(until)
    if since is None or until is None:
        raise HTTPException(status_code=400, detail={"error":"informe ambos since e until"})
    ds = datetime.fromtimestamp(int(since), tz=timezone.utc)
    du = datetime.fromtimestamp(int(until), tz=timezone.utc)
    if ds.year != du.year or ds.month != du.month:
        raise HTTPException(status_code=400, detail={"error":"intervalo deve estar dentro do mesmo mês"})
    first = datetime(ds.year, ds.month, 1, tzinfo=timezone.utc)
    if ds.month == 12:
        next_first = datetime(ds.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_first = datetime(ds.year, ds.month + 1, 1, tzinfo=timezone.utc)
    last_ts = int(next_first.timestamp()) - 1
    now = datetime.now(timezone.utc)
    if ds.year == now.year and ds.month == now.month:
        until = min(last_ts, int(now.timestamp()))
    else:
        until = last_ts
    since = int(first.timestamp())
    params = {"metric": ",".join(mets), "period": period, "metric_type": metric_type, "since": since, "until": until}
    def _fetch_single(p):
        return _graph_get(f"{_env_ig_id()}/insights", p)
    span = int(until) - int(since)
    max_span = 2592000
    if span > max_span:
        from datetime import timedelta
        agg: dict[str, int] = {}
        cur_start = datetime.fromtimestamp(since, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(until, tz=timezone.utc)
        chunks = 0
        while cur_start <= end_dt:
            ce = cur_start + timedelta(days=30)
            if ce > end_dt:
                ce = end_dt
            p = dict(params)
            p["since"] = int(cur_start.replace(tzinfo=timezone.utc).timestamp())
            p["until"] = int(ce.replace(tzinfo=timezone.utc).timestamp())
            r = _fetch_single(p)
            data = r.get("data") if isinstance(r, dict) else []
            for item in (data or []):
                name = str(item.get("name") or "").strip()
                tv = item.get("total_value") or {}
                val = tv.get("value")
                if val is None:
                    continue
                try:
                    v = int(val)
                except Exception:
                    try:
                        v = int(float(val))
                    except Exception:
                        v = 0
                agg[name] = agg.get(name, 0) + v
            chunks += 1
            cur_start = ce + timedelta(seconds=1)
            if cur_start > end_dt:
                break
        res = {"data": []}
        for name, v in agg.items():
            res["data"].append({"name": name, "period": period, "total_value": {"value": v}})
        igid = int(os.environ.get("IG_ACCOUNT_ID") or 0)
        ok, err = _persist_monthly_insights(res, igid, ds.year, ds.month)
        return res
    res = _fetch_single(params)
    igid = int(os.environ.get("IG_ACCOUNT_ID") or 0)
    ok, err = _persist_monthly_insights(res, igid, ds.year, ds.month)
    return res

def get_insights_posts(media_id: str, metric: str):
    mets = [m.strip() for m in (metric or "").split(",") if m.strip()]
    if not mets:
        raise HTTPException(status_code=400, detail={"error":"metric é obrigatório"})
    if any(m == "impressions" for m in mets):
        raise HTTPException(status_code=400, detail={"error":"'impressions' está deprecada; use 'views'"})
    media = _graph_get(f"{media_id}", {"fields": "id,media_type,timestamp,caption,permalink,media_url"})
    params = {"metric": ",".join(mets)}
    res = _graph_get(f"{media_id}/insights", params)
    if isinstance(res, dict):
        ok, err = _persist_post_insights(media, res)
    return res

def exchange_token_service(fb_exchange_token: str):
    base = "https://graph.facebook.com/v21.0"
    cid = os.environ.get("META_CLIENT_ID")
    csec = os.environ.get("META_CLIENT_SECRET")
    if not cid or not csec:
        raise HTTPException(status_code=500, detail="META_CLIENT_ID ou META_CLIENT_SECRET ausente")
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": cid,
        "client_secret": csec,
        "fb_exchange_token": fb_exchange_token,
    }
    url = base + "/oauth/access_token"
    r = requests.get(url, params=params, timeout=60)
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = {"error": r.text, "status": r.status_code}
        raise HTTPException(status_code=r.status_code, detail=detail)
    data = r.json()
    access_token = data.get("access_token")
    raw_expires_in = data.get("expires_in")
    if not access_token:
        raise HTTPException(status_code=500, detail={"error":"resposta inválida do oauth"})
    try:
        expires_in = int(raw_expires_in) if raw_expires_in is not None else 5184000
    except Exception:
        expires_in = 5184000
    now = datetime.now(timezone.utc)
    expires_at = now.replace(microsecond=0) + timedelta(seconds=expires_in)
    s = get_session()
    obj = s.get(OAuthToken, "meta")
    if obj is None:
        obj = OAuthToken(provider="meta")
    obj.access_token = access_token
    obj.expires_at = expires_at
    s.add(obj)
    s.commit()
    s.close()
    return {"access_token": access_token, "expires_in": int(expires_in)}