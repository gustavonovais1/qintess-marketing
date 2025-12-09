from fastapi import FastAPI, HTTPException, Query
import os
import requests
import uvicorn
from datetime import datetime, timezone
import psycopg2

app = FastAPI()

def _graph_get(path: str, extra_params: dict):
    base = os.environ.get("META_GRAPH_BASE") or "https://graph.facebook.com/v24.0"
    token = os.environ.get("META_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="META_ACCESS_TOKEN ausente")
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

def _env_page_id() -> str:
    pid = os.environ.get("PAGE_ID")
    if not pid:
        raise HTTPException(status_code=500, detail="PAGE_ID ausente no ambiente")
    return pid

def _env_ig_id() -> str:
    iid = os.environ.get("IG_ACCOUNT_ID")
    if not iid:
        raise HTTPException(status_code=500, detail="IG_ACCOUNT_ID ausente no ambiente")
    return iid

def _db_connect():
    host = os.environ.get("POSTGRES_HOST")
    db = os.environ.get("POSTGRES_DB")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    port = int(os.environ.get("POSTGRES_PORT") or 5432)
    try:
        return psycopg2.connect(host=host, dbname=db, user=user, password=password, port=port)
    except Exception:
        try:
            return psycopg2.connect(host="host.docker.internal", dbname=db, user=user, password=password, port=port)
        except Exception:
            raise

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
        conn = _db_connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO instagram.insights (
                ig_account_id, year, month,
                reach, website_clicks, profile_views, accounts_engaged, total_interactions,
                likes, comments, shares, saves, replies, follows_and_unfollows,
                profile_links_taps, views, reposts, content_views
            ) VALUES (
                %s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s
            )
            ON CONFLICT (ig_account_id, year, month) DO UPDATE SET
                reach = EXCLUDED.reach,
                website_clicks = EXCLUDED.website_clicks,
                profile_views = EXCLUDED.profile_views,
                accounts_engaged = EXCLUDED.accounts_engaged,
                total_interactions = EXCLUDED.total_interactions,
                likes = EXCLUDED.likes,
                comments = EXCLUDED.comments,
                shares = EXCLUDED.shares,
                saves = EXCLUDED.saves,
                replies = EXCLUDED.replies,
                follows_and_unfollows = EXCLUDED.follows_and_unfollows,
                profile_links_taps = EXCLUDED.profile_links_taps,
                views = EXCLUDED.views,
                reposts = EXCLUDED.reposts,
                content_views = EXCLUDED.content_views,
                updated_at = NOW()
            """,
            (
                int(ig_account_id), int(year), int(month),
                vals["reach"], vals["website_clicks"], vals["profile_views"], vals["accounts_engaged"], vals["total_interactions"],
                vals["likes"], vals["comments"], vals["shares"], vals["saves"], vals["replies"], vals["follows_and_unfollows"],
                vals["profile_links_taps"], vals["views"], vals["reposts"], vals["content_views"],
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        print("persisted instagram.insights", ig_account_id, year, month)
        return True, None
    except Exception as e:
        try:
            err = str(e)
        except Exception:
            err = "erro desconhecido"
        try:
            print("persistence_error instagram.insights", err)
        except Exception:
            pass
        return False, err

@app.get("/")
def root():
    return {
        "status": "ok",
        "graph_base": os.environ.get("META_GRAPH_BASE"),
        "page_id": os.environ.get("PAGE_ID"),
        "ig_account_id": os.environ.get("IG_ACCOUNT_ID")
    }

@app.get("/page/instagram_business_account")
def get_instagram_business_account_default():
    return _graph_get(f"{_env_page_id()}", {"fields": "instagram_business_account"})

@app.get("/ig/media")
def list_media_default():
    return _graph_get(f"{_env_ig_id()}/media", {})

@app.get("/ig/profile")
def get_profile_default(fields: str = Query("id,username,name,profile_picture_url,biography,followers_count,follows_count,media_count,website")):
    return _graph_get(f"{_env_ig_id()}", {"fields": fields})

@app.get("/ig/insights/profile")
def get_profile_insights_default(metric: str = Query("reach,website_clicks,profile_views,accounts_engaged,total_interactions,follows_and_unfollows,profile_links_taps"), period: str = Query("day"), metric_type: str = Query("total_value")):
    """
    Obtém métricas de perfil para a conta do Instagram.

    Parâmetros:
    - metric: Métricas a serem obtidas: reach, follower_count, website_clicks, profile_views, online_followers, accounts_engaged, total_interactions, likes, comments, shares, saves, replies, engaged_audience_demographics, reached_audience_demographics, follower_demographics, follows_and_unfollows, profile_links_taps, views, threads_likes, threads_replies, reposts, quotes, threads_followers, threads_follower_demographics, content_views, threads_views, threads_clicks, threads_reposts
    - period: Período de tempo para a métrica: day, week, days_28, month, lifetime, total_over_range.
    - metric_type: Tipo de métrica: total_value, default, time_series".
    """
    return _graph_get(f"{_env_ig_id()}/insights", {"metric": metric, "period": period, "metric_type": metric_type})

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
    # depreciação: impressions foi substituída por views
    if any(m == "impressions" for m in metrics):
        raise HTTPException(status_code=400, detail={"error":"'impressions' está deprecada a partir da v22.0; use 'views'"})

    # validar métricas desconhecidas
    unknown = [m for m in metrics if m not in allowed_metrics]
    if unknown:
        raise HTTPException(status_code=400, detail={"error":"métricas inválidas","metrics":unknown})

    # validar metric_type
    if metric_type and metric_type not in ("time_series","total_value"):
        raise HTTPException(status_code=400, detail={"error":"metric_type inválido; use 'time_series' ou 'total_value'"})

    # validar breakdown
    if breakdown:
        allowed_breakdowns = {"contact_button_type","follow_type","media_product_type"}
        if breakdown not in allowed_breakdowns:
            raise HTTPException(status_code=400, detail={"error":"breakdown inválido","allowed":list(allowed_breakdowns)})
        if (metric_type or "") != "total_value":
            raise HTTPException(status_code=400, detail={"error":"breakdown requer metric_type=total_value"})

    # conjuntos por categoria
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

    # demografia
    if any(m in demo for m in metrics):
        if timeframe is None:
            raise HTTPException(status_code=400, detail={"error":"timeframe é obrigatório para métricas demográficas"})
        if period is not None:
            raise HTTPException(status_code=400, detail={"error":"period não deve ser usado com métricas demográficas"})
        if metric_type:
            raise HTTPException(status_code=400, detail={"error":"metric_type não é suportado para métricas demográficas"})

    # online_followers
    if any(m == "online_followers" for m in metrics):
        if (period or "") != "lifetime":
            raise HTTPException(status_code=400, detail={"error":"online_followers requer period=lifetime"})

    # follower_count restrição
    if any(m == "follower_count" for m in metrics):
        if (period or "") != "day":
            raise HTTPException(status_code=400, detail={"error":"follower_count requer period=day"})

    # time-series exige period
    if any(m in ts for m in metrics):
        if period is None:
            raise HTTPException(status_code=400, detail={"error":"period é obrigatório para métricas time-series"})

    # totals requer metric_type=total_value e não devem usar period
    if any(m in totals for m in metrics):
        if (metric_type or "") != "total_value":
            raise HTTPException(status_code=400, detail={"error":"métricas de engajamento agregado requerem metric_type=total_value"})
        if period is None:
            raise HTTPException(status_code=400, detail={"error":"period é obrigatório para metric_type=total_value"})

@app.get("/ig/insights")
def insights_unified(metric: str = "reach, website_clicks, profile_views, accounts_engaged, total_interactions, likes, comments, shares, saves, replies, follows_and_unfollows, profile_links_taps, views, reposts, content_views", period: str = "day", timeframe: str | None = None, metric_type: str = "total_value", breakdown: str | None = None, since: int | str | None = None, until: int | str | None = None):
    mets = [m.strip() for m in (metric or "").split(",") if m.strip()]
    if not mets:
        raise HTTPException(status_code=400, detail={"error":"metric é obrigatório"})
    _validate_insights_params(mets, period, timeframe, metric_type, breakdown)
    # validar period values
    if period is not None:
        allowed_periods = {"day","week","days_28","month","lifetime"}
        if period not in allowed_periods:
            raise HTTPException(status_code=400, detail={"error":"period inválido","allowed":list(allowed_periods)})
    dem_metrics_default_block = {"engaged_audience_demographics","reached_audience_demographics","follower_demographics","threads_follower_demographics"}
    if since is None and until is None and not any(m in dem_metrics_default_block for m in mets) and not any(m == "online_followers" for m in mets):
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
    if since is not None and until is not None:
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
    # validar since/until
    if since is not None or until is not None:
        if since is None or until is None:
            raise HTTPException(status_code=400, detail={"error":"informe ambos since e until"})
        if not isinstance(since, int) or not isinstance(until, int) or since <= 0 or until <= 0:
            raise HTTPException(status_code=400, detail={"error":"since/until devem ser timestamps unix positivos"})
        if since >= until:
            raise HTTPException(status_code=400, detail={"error":"since deve ser menor que until"})
        demo_metrics = {"engaged_audience_demographics","reached_audience_demographics","follower_demographics","threads_follower_demographics"}
        if any(m in demo_metrics for m in mets):
            raise HTTPException(status_code=400, detail={"error":"para métricas demográficas use timeframe; since/until não são suportados"})
        if any(m == "online_followers" for m in mets):
            raise HTTPException(status_code=400, detail={"error":"online_followers não suporta since/until; use period=lifetime"})
    params = {"metric": ",".join(mets)}
    if period is not None:
        params["period"] = period
    if timeframe is not None:
        params["timeframe"] = timeframe
    if metric_type is not None:
        params["metric_type"] = metric_type
    if breakdown is not None:
        params["breakdown"] = breakdown
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    def _fetch_single(p):
        return _graph_get(f"{_env_ig_id()}/insights", p)

    # quebra intervalos >30 dias em janelas e agrega (apenas total_value)
    if (metric_type or "") == "total_value" and since is not None and until is not None:
        ds = datetime.fromtimestamp(int(since), tz=timezone.utc)
        du = datetime.fromtimestamp(int(until), tz=timezone.utc)
        span = int(until) - int(since)
        max_span = 2592000  # 30 dias em segundos
        if span > max_span:
            agg: dict[str, int] = {}
            cur_start = ds
            chunks = 0
            while cur_start <= du:
                cur_end = cur_start + (du - du)  # placeholder
                # define fim do chunk: 30 dias a partir do início ou du, o que vier primeiro
                ce = cur_start + (du - du)  # reset
                try:
                    ce = cur_start + (du - du)
                except Exception:
                    ce = cur_start
                # usar 30 dias exatos
                from datetime import timedelta
                ce = cur_start + timedelta(days=30)
                if ce > du:
                    ce = du
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
                if cur_start > du:
                    break
            # monta payload agregado
            res = {"data": [], "chunked": True, "chunks": chunks}
            for name, v in agg.items():
                res["data"].append({"name": name, "period": period, "total_value": {"value": v}})
            # persist
            igid = int(os.environ.get("IG_ACCOUNT_ID") or 0)
            ok, err = _persist_monthly_insights(res, igid, ds.year, ds.month)
            try:
                res["persisted"] = ok
                if not ok:
                    res["persistence_error"] = err
            except Exception:
                pass
            return res

    # chamada simples
    res = _fetch_single(params)
    if (metric_type or "") == "total_value":
        ds = datetime.fromtimestamp(int(since), tz=timezone.utc) if since is not None else datetime.now(timezone.utc)
        igid = int(os.environ.get("IG_ACCOUNT_ID") or 0)
        ok, err = _persist_monthly_insights(res, igid, ds.year, ds.month)
        try:
            if isinstance(res, dict):
                res["persisted"] = ok
                if not ok:
                    res["persistence_error"] = err
        except Exception:
            pass
    return res

@app.get("/health/db")
def health_db():
    info = {
        "host": os.environ.get("DB_HOST"),
        "name": os.environ.get("DB_NAME"),
        "user": os.environ.get("DB_USER"),
        "port": int(os.environ.get("DB_PORT") or 5432),
    }
    try:
        conn = _db_connect()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        one = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM instagram.insights")
        cnt = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"ok": True, "select_one": one[0] if one else None, "rows": cnt, "db": info}
    except Exception as e:
        try:
            msg = str(e)
        except Exception:
            msg = "erro desconhecido"
        return {"ok": False, "error": msg, "db": info}

@app.get("/oauth/exchange_token")
def exchange_token(fb_exchange_token: str = Query(...)):
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
    try:
        return r.json()
    except Exception:
        return {"raw": r.text}

def main():
    port = int(os.environ.get("PORT") or 8000)
    uvicorn.run("instagram.app:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()


