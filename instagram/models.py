from sqlalchemy import Column, Integer, BigInteger, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from .db import Base

class InsightsProfile(Base):
    __tablename__ = "insights_profile"
    __table_args__ = {"schema": "instagram"}

    ig_account_id = Column(Integer, primary_key=True)
    year = Column(Integer, primary_key=True)
    month = Column(Integer, primary_key=True)

    reach = Column(BigInteger)
    website_clicks = Column(BigInteger)
    profile_views = Column(BigInteger)
    accounts_engaged = Column(BigInteger)
    total_interactions = Column(BigInteger)
    likes = Column(BigInteger)
    comments = Column(BigInteger)
    shares = Column(BigInteger)
    saves = Column(BigInteger)
    replies = Column(BigInteger)
    follows_and_unfollows = Column(BigInteger)
    profile_links_taps = Column(BigInteger)
    views = Column(BigInteger)
    reposts = Column(BigInteger)
    content_views = Column(BigInteger)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class InsightsPost(Base):
    __tablename__ = "insights_posts"
    __table_args__ = {"schema": "instagram"}

    media_id = Column(Text, primary_key=True)
    media_type = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    caption = Column(Text)
    permalink = Column(Text)
    media_url = Column(Text)

    views = Column(BigInteger)
    reach = Column(BigInteger)
    saves = Column(BigInteger)
    likes = Column(BigInteger)
    comments = Column(BigInteger)
    shares = Column(BigInteger)
    total_interactions = Column(BigInteger)
    follows = Column(BigInteger)
    profile_visits = Column(BigInteger)
    profile_activity = Column(BigInteger)
    reposts = Column(BigInteger)

    ig_reels_video_view_total_time = Column(BigInteger)
    ig_reels_avg_watch_time = Column(Float)
    reels_skip_rate = Column(Float)
    facebook_views = Column(BigInteger)
    crossposted_views = Column(BigInteger)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class OAuthToken(Base):
    __tablename__ = "oauth_token"
    __table_args__ = {"schema": "instagram"}

    provider = Column(Text, primary_key=True)
    access_token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)