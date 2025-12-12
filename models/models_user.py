from sqlalchemy import Column, Integer, Text
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
from core.db import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "user"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    password_salt = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
