import os

def start_linkedin_bot(segments: str | None = None):
    import subprocess, sys
    args = [sys.executable, "-m", "bot.linkedin.src.main"]
    storage = "linkedin_storage.json"
    args += ["--storage", storage]
    env = os.environ.copy()
    env["DEFAULT_SEGMENTS"] = segments or "updates,visitors,followers,competitors"
    env["DB_HOST"] = env.get("POSTGRES_HOST") or env.get("DB_HOST") or "localhost"
    env["DB_NAME"] = env.get("POSTGRES_DB") or env.get("DB_NAME") or "postgres"
    env["DB_USER"] = env.get("POSTGRES_USER") or env.get("DB_USER") or "postgres"
    env["DB_PASSWORD"] = env.get("POSTGRES_PASSWORD") or env.get("DB_PASSWORD") or ""
    p = subprocess.Popen(args, env=env)
    return {"pid": p.pid, "started": True}
