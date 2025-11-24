import os
import re
import datetime
import calendar
import pandas as pd
import psycopg2

def _get_env(name, default=None):
    v = os.environ.get(name)
    return v if v is not None else default

def _connect():
    host = _get_env("DB_HOST", "localhost")
    db = _get_env("DB_NAME", "postgres")
    user = _get_env("DB_USER", "postgres")
    password = _get_env("DB_PASSWORD", "")
    return psycopg2.connect(host=host, dbname=db, user=user, password=password)

def _ensure_schema_and_tables(conn):
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS linkedin")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS linkedin.competitors (
            period text,
            page text,
            total_followers integer,
            new_followers integer,
            total_post_engagements integer,
            total_posts integer
        )
        """
    )
    try:
        cur.execute("DROP INDEX IF EXISTS linkedin.competitors_period_idx")
    except Exception:
        pass
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS competitors_period_page_idx ON linkedin.competitors(period, page)")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS linkedin.followers (
            date date,
            sponsored_followers integer,
            organic_followers integer,
            auto_invited_followers integer,
            total_followers integer
        )
        """
    )
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS followers_date_idx ON linkedin.followers(date)")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS linkedin.updates (
            date date,
            impressions_organic integer,
            impressions_sponsored integer,
            impressions_total integer,
            unique_impressions_organic integer,
            clicks_organic integer,
            clicks_sponsored integer,
            clicks_total integer,
            reactions_organic integer,
            reactions_sponsored integer,
            reactions_total integer,
            comments_organic integer,
            comments_sponsored integer,
            comments_total integer,
            shares_organic integer,
            shares_sponsored integer,
            shares_total integer,
            engagement_rate_organic numeric(10,4),
            engagement_rate_sponsored numeric(10,4),
            engagement_rate_total numeric(10,4)
        )
        """
    )
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS updates_date_idx ON linkedin.updates(date)")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS linkedin.visitors (
            date date,
            overview_page_views_desktop integer,
            overview_page_views_mobile integer,
            overview_page_views_total integer,
            overview_unique_visitors_desktop integer,
            overview_unique_visitors_mobile integer,
            overview_unique_visitors_total integer,
            day_by_day_page_views_desktop integer,
            day_by_day_page_views_mobile integer,
            day_by_day_page_views_total integer,
            day_by_day_unique_visitors_desktop integer,
            day_by_day_unique_visitors_mobile integer,
            day_by_day_unique_visitors_total integer,
            jobs_page_views_desktop integer,
            jobs_page_views_mobile integer,
            jobs_page_views_total integer,
            jobs_unique_visitors_desktop integer,
            jobs_unique_visitors_mobile integer,
            jobs_unique_visitors_total integer,
            total_page_views_desktop integer,
            total_page_views_mobile integer,
            total_page_views_total integer,
            total_unique_visitors_desktop integer,
            total_unique_visitors_mobile integer,
            total_unique_visitors_total integer
        )
        """
    )
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS visitors_date_idx ON linkedin.visitors(date)")
    conn.commit()
    cur.close()

def _month_period_string(dt):
    name = calendar.month_name[dt.month].lower()
    return f"{name}/{dt.year}"

def _read_excel_raw(path):
    ext = os.path.splitext(path)[1].lower()
    engine = "openpyxl" if ext == ".xlsx" else "xlrd"
    return pd.read_excel(path, engine=engine, header=None)

def _find_header_row(df: pd.DataFrame, kind: str | None) -> int | None:
    try:
        max_scan = min(len(df), 50)
        for i in range(max_scan):
            row = [str(x).strip() for x in list(df.iloc[i].values)]
            if kind == "competitors":
                if any(x.lower() == "page" for x in row):
                    return i
            else:
                if any(x.lower() == "data" for x in row):
                    return i
        return None
    except Exception:
        return None

def _read_excel_structured(path, kind):
    dfr = _read_excel_raw(path)
    hdr = _find_header_row(dfr, kind)
    if hdr is None:
        return dfr
    header = [str(x).strip() for x in list(dfr.iloc[hdr].values)]
    df = dfr.iloc[hdr + 1:].copy()
    df.columns = header
    # drop fully empty rows
    try:
        df = df.dropna(how="all")
    except Exception:
        pass
    return df

def _to_int(s):
    try:
        return int(s) if pd.notna(s) else None
    except Exception:
        try:
            return int(float(str(s).replace("%", "").replace(",", ".")))
        except Exception:
            return None

def _to_rate(s):
    if pd.isna(s):
        return None
    try:
        if isinstance(s, str) and "%" in s:
            v = float(s.replace("%", "").replace(",", ".")) / 100.0
            return v
        return float(s)
    except Exception:
        try:
            return float(str(s).replace(",", "."))
        except Exception:
            return None

def _to_date(s):
    if pd.isna(s):
        return None
    if isinstance(s, datetime.date):
        return s
    if isinstance(s, datetime.datetime):
        return s.date()
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S"]:
        try:
            return datetime.datetime.strptime(str(s), fmt).date()
        except Exception:
            continue
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None

def _parse_period_from_filename(fn: str) -> str:
    m = re.search(r"_(\d{2})-(\d{2})-(\d{4})_(\d{2})-(\d{2})-(\d{4})", fn)
    if m:
        try:
            end = datetime.date(int(m.group(6)), int(m.group(5)), int(m.group(4)))
            return _month_period_string(end)
        except Exception:
            pass
    now = datetime.datetime.utcnow()
    return _month_period_string(now)

def _process_competitors(df, conn, source_name: str):
    period = _parse_period_from_filename(source_name)
    mapping = {
        "Page": "page",
        "Total de seguidores": "total_followers",
        "Novos seguidores": "new_followers",
        "Total de engajamentos da publicação": "total_post_engagements",
        "Total de publicações": "total_posts",
    }
    cols = {k: v for k, v in mapping.items() if k in df.columns}
    dfo = df.rename(columns=cols)
    dfo["total_followers"] = dfo.get("total_followers", pd.Series(dtype="float")).apply(_to_int)
    dfo["new_followers"] = dfo.get("new_followers", pd.Series(dtype="float")).apply(_to_int)
    dfo["total_post_engagements"] = dfo.get("total_post_engagements", pd.Series(dtype="float")).apply(_to_int)
    dfo["total_posts"] = dfo.get("total_posts", pd.Series(dtype="float")).apply(_to_int)
    cur = conn.cursor()
    cnt = 0
    for _, row in dfo.iterrows():
        cur.execute(
            """
            INSERT INTO linkedin.competitors(period, page, total_followers, new_followers, total_post_engagements, total_posts)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (period, page) DO UPDATE SET
                page = EXCLUDED.page,
                total_followers = EXCLUDED.total_followers,
                new_followers = EXCLUDED.new_followers,
                total_post_engagements = EXCLUDED.total_post_engagements,
                total_posts = EXCLUDED.total_posts
            """,
            (
                period,
                row.get("page"),
                row.get("total_followers"),
                row.get("new_followers"),
                row.get("total_post_engagements"),
                row.get("total_posts"),
            ),
        )
        cnt += 1
    conn.commit()
    cur.close()
    return cnt

def _process_followers(df, conn):
    mapping = {
        "Data": "date",
        "Seguidores patrocinados": "sponsored_followers",
        "Seguidores orgânicos": "organic_followers",
        "Seguidores convidados automaticamente": "auto_invited_followers",
        "Total de seguidores": "total_followers",
    }
    cols = {k: v for k, v in mapping.items() if k in df.columns}
    dfo = df.rename(columns=cols)
    dfo["date"] = dfo.get("date", pd.Series(dtype="object")).apply(_to_date)
    dfo["sponsored_followers"] = dfo.get("sponsored_followers", pd.Series(dtype="float")).apply(_to_int)
    dfo["organic_followers"] = dfo.get("organic_followers", pd.Series(dtype="float")).apply(_to_int)
    dfo["auto_invited_followers"] = dfo.get("auto_invited_followers", pd.Series(dtype="float")).apply(_to_int)
    dfo["total_followers"] = dfo.get("total_followers", pd.Series(dtype="float")).apply(_to_int)
    cur = conn.cursor()
    cnt = 0
    for _, row in dfo.iterrows():
        if not row.get("date"):
            continue
        cur.execute(
            """
            INSERT INTO linkedin.followers(date, sponsored_followers, organic_followers, auto_invited_followers, total_followers)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                sponsored_followers = EXCLUDED.sponsored_followers,
                organic_followers = EXCLUDED.organic_followers,
                auto_invited_followers = EXCLUDED.auto_invited_followers,
                total_followers = EXCLUDED.total_followers
            """,
            (
                row.get("date"),
                row.get("sponsored_followers"),
                row.get("organic_followers"),
                row.get("auto_invited_followers"),
                row.get("total_followers"),
            ),
        )
        cnt += 1
    conn.commit()
    cur.close()
    return cnt

def _process_updates(df, conn):
    mapping = {
        "Data": "date",
        "Impressões (orgânicas)": "impressions_organic",
        "Impressões (patrocinadas)": "impressions_sponsored",
        "Impressões (total)": "impressions_total",
        "Impressões únicas (orgânicas)": "unique_impressions_organic",
        "Cliques (orgânicos)": "clicks_organic",
        "Cliques (patrocinados)": "clicks_sponsored",
        "Cliques (total)": "clicks_total",
        "Reações (orgânicas)": "reactions_organic",
        "Reações (patrocinadas)": "reactions_sponsored",
        "Reações (total)": "reactions_total",
        "Comentários (orgânicos)": "comments_organic",
        "Comentários (patrocinados)": "comments_sponsored",
        "Comentários (total)": "comments_total",
        "Compartilhamentos (orgânicos)": "shares_organic",
        "Compartilhamentos (patrocinados)": "shares_sponsored",
        "Compartilhamentos (total)": "shares_total",
        "Taxa de engajamento (orgânico)": "engagement_rate_organic",
        "Taxa de engajamento (patrocinado)": "engagement_rate_sponsored",
        "Taxa de engajamento (total)": "engagement_rate_total",
    }
    cols = {k: v for k, v in mapping.items() if k in df.columns}
    dfo = df.rename(columns=cols)
    dfo["date"] = dfo.get("date", pd.Series(dtype="object")).apply(_to_date)
    for k in [
        "impressions_organic",
        "impressions_sponsored",
        "impressions_total",
        "unique_impressions_organic",
        "clicks_organic",
        "clicks_sponsored",
        "clicks_total",
        "reactions_organic",
        "reactions_sponsored",
        "reactions_total",
        "comments_organic",
        "comments_sponsored",
        "comments_total",
        "shares_organic",
        "shares_sponsored",
        "shares_total",
    ]:
        dfo[k] = dfo.get(k, pd.Series(dtype="float")).apply(_to_int)
    for k in [
        "engagement_rate_organic",
        "engagement_rate_sponsored",
        "engagement_rate_total",
    ]:
        dfo[k] = dfo.get(k, pd.Series(dtype="float")).apply(_to_rate)
    cur = conn.cursor()
    cnt = 0
    for _, row in dfo.iterrows():
        if not row.get("date"):
            continue
        cur.execute(
            """
            INSERT INTO linkedin.updates(
                date,
                impressions_organic,
                impressions_sponsored,
                impressions_total,
                unique_impressions_organic,
                clicks_organic,
                clicks_sponsored,
                clicks_total,
                reactions_organic,
                reactions_sponsored,
                reactions_total,
                comments_organic,
                comments_sponsored,
                comments_total,
                shares_organic,
                shares_sponsored,
                shares_total,
                engagement_rate_organic,
                engagement_rate_sponsored,
                engagement_rate_total
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
            ON CONFLICT (date) DO UPDATE SET
                impressions_organic = EXCLUDED.impressions_organic,
                impressions_sponsored = EXCLUDED.impressions_sponsored,
                impressions_total = EXCLUDED.impressions_total,
                unique_impressions_organic = EXCLUDED.unique_impressions_organic,
                clicks_organic = EXCLUDED.clicks_organic,
                clicks_sponsored = EXCLUDED.clicks_sponsored,
                clicks_total = EXCLUDED.clicks_total,
                reactions_organic = EXCLUDED.reactions_organic,
                reactions_sponsored = EXCLUDED.reactions_sponsored,
                reactions_total = EXCLUDED.reactions_total,
                comments_organic = EXCLUDED.comments_organic,
                comments_sponsored = EXCLUDED.comments_sponsored,
                comments_total = EXCLUDED.comments_total,
                shares_organic = EXCLUDED.shares_organic,
                shares_sponsored = EXCLUDED.shares_sponsored,
                shares_total = EXCLUDED.shares_total,
                engagement_rate_organic = EXCLUDED.engagement_rate_organic,
                engagement_rate_sponsored = EXCLUDED.engagement_rate_sponsored,
                engagement_rate_total = EXCLUDED.engagement_rate_total
            """,
            (
                row.get("date"),
                row.get("impressions_organic"),
                row.get("impressions_sponsored"),
                row.get("impressions_total"),
                row.get("unique_impressions_organic"),
                row.get("clicks_organic"),
                row.get("clicks_sponsored"),
                row.get("clicks_total"),
                row.get("reactions_organic"),
                row.get("reactions_sponsored"),
                row.get("reactions_total"),
                row.get("comments_organic"),
                row.get("comments_sponsored"),
                row.get("comments_total"),
                row.get("shares_organic"),
                row.get("shares_sponsored"),
                row.get("shares_total"),
                row.get("engagement_rate_organic"),
                row.get("engagement_rate_sponsored"),
                row.get("engagement_rate_total"),
            ),
        )
        cnt += 1
    conn.commit()
    cur.close()
    return cnt

def _process_visitors(df, conn):
    mapping = {
        "Data": "date",
        "Visualizações da página Visão geral (computadores)": "overview_page_views_desktop",
        "Visualizações da página Visão geral (dispositivos móveis)": "overview_page_views_mobile",
        "Visualizações da página Visão geral (total)": "overview_page_views_total",
        "Visitantes únicos da página Visão geral (computadores)": "overview_unique_visitors_desktop",
        "Visitantes únicos da página Visão geral (dispositivos móveis)": "overview_unique_visitors_mobile",
        "Visitantes únicos da página Visão geral (total)": "overview_unique_visitors_total",
        "Visualizações da página Dia a dia (computadores)": "day_by_day_page_views_desktop",
        "Visualizações da página Dia a dia (dispositivos móveis)": "day_by_day_page_views_mobile",
        "Visualizações da página Dia a dia (total)": "day_by_day_page_views_total",
        "Visitantes únicos da página Dia a dia (computadores)": "day_by_day_unique_visitors_desktop",
        "Visitantes únicos da página Dia a dia (dispositivos móveis)": "day_by_day_unique_visitors_mobile",
        "Visitantes únicos da página Dia a dia (total)": "day_by_day_unique_visitors_total",
        "Visualizações da página Vagas (computadores)": "jobs_page_views_desktop",
        "Visualizações da página Vagas (dispositivos móveis)": "jobs_page_views_mobile",
        "Visualizações da página Vagas (total)": "jobs_page_views_total",
        "Visitantes únicos da página Vagas (computadores)": "jobs_unique_visitors_desktop",
        "Visitantes únicos da página Vagas (dispositivos móveis)": "jobs_unique_visitors_mobile",
        "Visitantes únicos da página Vagas (total)": "jobs_unique_visitors_total",
        "Total de visualizações da página (computadores)": "total_page_views_desktop",
        "Total de visualizações da página (dispositivos móveis)": "total_page_views_mobile",
        "Total de visualizações da página (total)": "total_page_views_total",
        "Total de visitantes únicos (computadores)": "total_unique_visitors_desktop",
        "Total de visitantes únicos (dispositivos móveis)": "total_unique_visitors_mobile",
        "Total de visitantes únicos (total)": "total_unique_visitors_total",
    }
    cols = {k: v for k, v in mapping.items() if k in df.columns}
    dfo = df.rename(columns=cols)
    dfo["date"] = dfo.get("date", pd.Series(dtype="object")).apply(_to_date)
    for k in [
        "overview_page_views_desktop",
        "overview_page_views_mobile",
        "overview_page_views_total",
        "overview_unique_visitors_desktop",
        "overview_unique_visitors_mobile",
        "overview_unique_visitors_total",
        "day_by_day_page_views_desktop",
        "day_by_day_page_views_mobile",
        "day_by_day_page_views_total",
        "day_by_day_unique_visitors_desktop",
        "day_by_day_unique_visitors_mobile",
        "day_by_day_unique_visitors_total",
        "jobs_page_views_desktop",
        "jobs_page_views_mobile",
        "jobs_page_views_total",
        "jobs_unique_visitors_desktop",
        "jobs_unique_visitors_mobile",
        "jobs_unique_visitors_total",
        "total_page_views_desktop",
        "total_page_views_mobile",
        "total_page_views_total",
        "total_unique_visitors_desktop",
        "total_unique_visitors_mobile",
        "total_unique_visitors_total",
    ]:
        dfo[k] = dfo.get(k, pd.Series(dtype="float")).apply(_to_int)
    cur = conn.cursor()
    cnt = 0
    for _, row in dfo.iterrows():
        if not row.get("date"):
            continue
        cur.execute(
            """
            INSERT INTO linkedin.visitors(
                date,
                overview_page_views_desktop,
                overview_page_views_mobile,
                overview_page_views_total,
                overview_unique_visitors_desktop,
                overview_unique_visitors_mobile,
                overview_unique_visitors_total,
                day_by_day_page_views_desktop,
                day_by_day_page_views_mobile,
                day_by_day_page_views_total,
                day_by_day_unique_visitors_desktop,
                day_by_day_unique_visitors_mobile,
                day_by_day_unique_visitors_total,
                jobs_page_views_desktop,
                jobs_page_views_mobile,
                jobs_page_views_total,
                jobs_unique_visitors_desktop,
                jobs_unique_visitors_mobile,
                jobs_unique_visitors_total,
                total_page_views_desktop,
                total_page_views_mobile,
                total_page_views_total,
                total_unique_visitors_desktop,
                total_unique_visitors_mobile,
                total_unique_visitors_total
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
            ON CONFLICT (date) DO UPDATE SET
                overview_page_views_desktop = EXCLUDED.overview_page_views_desktop,
                overview_page_views_mobile = EXCLUDED.overview_page_views_mobile,
                overview_page_views_total = EXCLUDED.overview_page_views_total,
                overview_unique_visitors_desktop = EXCLUDED.overview_unique_visitors_desktop,
                overview_unique_visitors_mobile = EXCLUDED.overview_unique_visitors_mobile,
                overview_unique_visitors_total = EXCLUDED.overview_unique_visitors_total,
                day_by_day_page_views_desktop = EXCLUDED.day_by_day_page_views_desktop,
                day_by_day_page_views_mobile = EXCLUDED.day_by_day_page_views_mobile,
                day_by_day_page_views_total = EXCLUDED.day_by_day_page_views_total,
                day_by_day_unique_visitors_desktop = EXCLUDED.day_by_day_unique_visitors_desktop,
                day_by_day_unique_visitors_mobile = EXCLUDED.day_by_day_unique_visitors_mobile,
                day_by_day_unique_visitors_total = EXCLUDED.day_by_day_unique_visitors_total,
                jobs_page_views_desktop = EXCLUDED.jobs_page_views_desktop,
                jobs_page_views_mobile = EXCLUDED.jobs_page_views_mobile,
                jobs_page_views_total = EXCLUDED.jobs_page_views_total,
                jobs_unique_visitors_desktop = EXCLUDED.jobs_unique_visitors_desktop,
                jobs_unique_visitors_mobile = EXCLUDED.jobs_unique_visitors_mobile,
                jobs_unique_visitors_total = EXCLUDED.jobs_unique_visitors_total,
                total_page_views_desktop = EXCLUDED.total_page_views_desktop,
                total_page_views_mobile = EXCLUDED.total_page_views_mobile,
                total_page_views_total = EXCLUDED.total_page_views_total,
                total_unique_visitors_desktop = EXCLUDED.total_unique_visitors_desktop,
                total_unique_visitors_mobile = EXCLUDED.total_unique_visitors_mobile,
                total_unique_visitors_total = EXCLUDED.total_unique_visitors_total
            """,
            (
                row.get("date"),
                row.get("overview_page_views_desktop"),
                row.get("overview_page_views_mobile"),
                row.get("overview_page_views_total"),
                row.get("overview_unique_visitors_desktop"),
                row.get("overview_unique_visitors_mobile"),
                row.get("overview_unique_visitors_total"),
                row.get("day_by_day_page_views_desktop"),
                row.get("day_by_day_page_views_mobile"),
                row.get("day_by_day_page_views_total"),
                row.get("day_by_day_unique_visitors_desktop"),
                row.get("day_by_day_unique_visitors_mobile"),
                row.get("day_by_day_unique_visitors_total"),
                row.get("jobs_page_views_desktop"),
                row.get("jobs_page_views_mobile"),
                row.get("jobs_page_views_total"),
                row.get("jobs_unique_visitors_desktop"),
                row.get("jobs_unique_visitors_mobile"),
                row.get("jobs_unique_visitors_total"),
                row.get("total_page_views_desktop"),
                row.get("total_page_views_mobile"),
                row.get("total_page_views_total"),
                row.get("total_unique_visitors_desktop"),
                row.get("total_unique_visitors_mobile"),
                row.get("total_unique_visitors_total"),
            ),
        )
        cnt += 1
    conn.commit()
    cur.close()
    return cnt

def ingest_downloads(downloads_dir):
    conn = _connect()
    _ensure_schema_and_tables(conn)
    files = []
    try:
        for name in os.listdir(downloads_dir):
            if name.lower().endswith((".xls", ".xlsx")):
                files.append(os.path.join(downloads_dir, name))
    except Exception:
        files = []
    for path in files:
        fn = os.path.basename(path)
        m = re.match(r"linkedin_(\w+)_", fn)
        kind = m.group(1) if m else ""
        processed = 0
        try:
            df = _read_excel_structured(path, kind)
        except Exception:
            df = None
        if df is None or df.empty:
            try:
                os.remove(path)
            except Exception:
                pass
            continue
        try:
            if kind == "competitors":
                processed = _process_competitors(df, conn, fn)
            elif kind == "followers":
                processed = _process_followers(df, conn)
            elif kind == "updates":
                processed = _process_updates(df, conn)
            elif kind == "visitors":
                processed = _process_visitors(df, conn)
        except Exception:
            processed = 0
        if processed > 0:
            try:
                os.remove(path)
            except Exception:
                pass
    conn.close()

if __name__ == "__main__":
    dd = _get_env("DOWNLOADS_DIR", "/app/downloads")
    ingest_downloads(dd)