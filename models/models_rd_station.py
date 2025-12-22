from sqlalchemy import Column, Text, DateTime, Integer, Float, BigInteger, Boolean
from sqlalchemy.sql import func
from core.db import Base

class RDToken(Base):
    __tablename__ = "rd_tokens"
    __table_args__ = {"schema": "rd_station"}

    id = Column(Text, primary_key=True, default="current")
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RDEmailAnalytics(Base):
    __tablename__ = "email_analytics"
    __table_args__ = {"schema": "rd_station"}

    campaign_id = Column(BigInteger, primary_key=True)
    campaign_name = Column(Text)
    send_at = Column(DateTime(timezone=True))
    email_dropped_count = Column(Integer)
    email_delivered_count = Column(Integer)
    email_bounced_count = Column(Integer)
    email_opened_count = Column(Integer)
    email_clicked_count = Column(Integer)
    email_unsubscribed_count = Column(Integer)
    email_spam_reported_count = Column(Integer)
    email_delivered_rate = Column(Float)
    email_opened_rate = Column(Float)
    email_clicked_rate = Column(Float)
    email_spam_reported_rate = Column(Float)
    contacts_count = Column(Integer)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RDConversionAnalytics(Base):
    __tablename__ = "conversion_analytics"
    __table_args__ = {"schema": "rd_station"}

    asset_id = Column(BigInteger, primary_key=True)
    asset_identifier = Column(Text)
    asset_created_at = Column(DateTime(timezone=True))
    asset_updated_at = Column(DateTime(timezone=True))
    assets_type = Column(Text)
    conversion_count = Column(Integer)
    visits_count = Column(Integer)
    conversion_rate = Column(Float)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RDSegmentation(Base):
    __tablename__ = "segmentations"
    __table_args__ = {"schema": "rd_station"}

    id = Column(BigInteger, primary_key=True)
    name = Column(Text)
    standard = Column(Boolean)
    process_status = Column(Text)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RDLandingPage(Base):
    __tablename__ = "landing_pages"
    __table_args__ = {"schema": "rd_station"}

    id = Column(BigInteger, primary_key=True)
    title = Column(Text)
    conversion_identifier = Column(Text)
    status = Column(Text)
    has_active_experiment = Column(Boolean)
    had_experiment = Column(Boolean)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RDWorkflow(Base):
    __tablename__ = "workflows"
    __table_args__ = {"schema": "rd_station"}

    id = Column(Text, primary_key=True)  # UUID
    name = Column(Text)
    user_email_created = Column(Text)
    user_email_updated = Column(Text)
    status = Column(Text)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
