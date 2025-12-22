import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

def _dsn():
    host = os.environ.get("POSTGRES_HOST")
    db = os.environ.get("POSTGRES_DB")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    port = os.environ.get("POSTGRES_PORT")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(_dsn(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

def get_session():
    return SessionLocal()

with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS instagram"))
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS linkedin"))
    conn.execute(text('CREATE SCHEMA IF NOT EXISTS "google_analytics"'))
    conn.execute(text('CREATE SCHEMA IF NOT EXISTS "user"'))
    conn.execute(text('CREATE SCHEMA IF NOT EXISTS "rd_station"'))

from models import *

# Criar todas as tabelas no banco de dados
Base.metadata.create_all(bind=engine)
