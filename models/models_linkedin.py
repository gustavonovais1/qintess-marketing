from sqlalchemy import Column, Text, Integer, Date, Numeric, UniqueConstraint
from db import Base


class Competitor(Base):
    __tablename__ = "competitors"
    __table_args__ = (
        UniqueConstraint("period", "page", name="competitors_period_page_idx"),
        {"schema": "linkedin"},
    )

    period = Column(Text, primary_key=True)
    page = Column(Text, primary_key=True)
    total_followers = Column(Integer)
    new_followers = Column(Integer)
    total_post_engagements = Column(Integer)
    total_posts = Column(Integer)


class Follower(Base):
    __tablename__ = "followers"
    __table_args__ = (
        {"schema": "linkedin"},
    )

    date = Column(Date, primary_key=True)
    sponsored_followers = Column(Integer)
    organic_followers = Column(Integer)
    auto_invited_followers = Column(Integer)
    total_followers = Column(Integer)


class Update(Base):
    __tablename__ = "updates"
    __table_args__ = (
        {"schema": "linkedin"},
    )

    date = Column(Date, primary_key=True)
    impressions_organic = Column(Integer)
    impressions_sponsored = Column(Integer)
    impressions_total = Column(Integer)
    unique_impressions_organic = Column(Integer)
    clicks_organic = Column(Integer)
    clicks_sponsored = Column(Integer)
    clicks_total = Column(Integer)
    reactions_organic = Column(Integer)
    reactions_sponsored = Column(Integer)
    reactions_total = Column(Integer)
    comments_organic = Column(Integer)
    comments_sponsored = Column(Integer)
    comments_total = Column(Integer)
    shares_organic = Column(Integer)
    shares_sponsored = Column(Integer)
    shares_total = Column(Integer)
    engagement_rate_organic = Column(Numeric(10, 4))
    engagement_rate_sponsored = Column(Numeric(10, 4))
    engagement_rate_total = Column(Numeric(10, 4))


class Visitor(Base):
    __tablename__ = "visitors"
    __table_args__ = (
        {"schema": "linkedin"},
    )

    date = Column(Date, primary_key=True)
    overview_page_views_desktop = Column(Integer)
    overview_page_views_mobile = Column(Integer)
    overview_page_views_total = Column(Integer)
    overview_unique_visitors_desktop = Column(Integer)
    overview_unique_visitors_mobile = Column(Integer)
    overview_unique_visitors_total = Column(Integer)
    day_by_day_page_views_desktop = Column(Integer)
    day_by_day_page_views_mobile = Column(Integer)
    day_by_day_page_views_total = Column(Integer)
    day_by_day_unique_visitors_desktop = Column(Integer)
    day_by_day_unique_visitors_mobile = Column(Integer)
    day_by_day_unique_visitors_total = Column(Integer)
    jobs_page_views_desktop = Column(Integer)
    jobs_page_views_mobile = Column(Integer)
    jobs_page_views_total = Column(Integer)
    jobs_unique_visitors_desktop = Column(Integer)
    jobs_unique_visitors_mobile = Column(Integer)
    jobs_unique_visitors_total = Column(Integer)
    total_page_views_desktop = Column(Integer)
    total_page_views_mobile = Column(Integer)
    total_page_views_total = Column(Integer)
    total_unique_visitors_desktop = Column(Integer)
    total_unique_visitors_mobile = Column(Integer)
    total_unique_visitors_total = Column(Integer)