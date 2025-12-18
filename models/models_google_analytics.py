from sqlalchemy import Column, Integer, BigInteger, Text, Numeric, Date
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
from core.db import Base

class GAUsers(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "google_analytics"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    country = Column(Text)
    device_category = Column(Text)
    active_users = Column(BigInteger)
    new_users = Column(BigInteger)
    total_users = Column(BigInteger)
    active_1_day_users = Column(BigInteger)
    active_7_day_users = Column(BigInteger)
    active_28_day_users = Column(BigInteger)
    dau_per_mau = Column(Numeric(10,6))
    dau_per_wau = Column(Numeric(10,6))
    wau_per_mau = Column(Numeric(10,6))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class GAEngagement(Base):
    __tablename__ = "engagement"
    __table_args__ = {"schema": "google_analytics"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    device_category = Column(Text)
    country = Column(Text)
    engaged_sessions = Column(BigInteger)
    engagement_rate = Column(Numeric(10,6))
    average_session_duration = Column(Integer)
    user_engagement_duration = Column(Integer)
    events_per_session = Column(Numeric(10,6))
    session_key_event_rate = Column(Numeric(10,6))
    user_key_event_rate = Column(Numeric(10,6))
    scrolled_users = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class GAEvents(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "google_analytics"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    event_name = Column(Text)
    page_path = Column(Text)
    event_count = Column(BigInteger)
    event_count_per_user = Column(Numeric(10,6))
    event_value = Column(Numeric(18,6))
    key_events = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class GAContent(Base):
    __tablename__ = "content"
    __table_args__ = {"schema": "google_analytics"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    page_title = Column(Text)
    page_path = Column(Text)
    screen_page_views = Column(BigInteger)
    screen_page_views_per_session = Column(Numeric(10,6))
    screen_page_views_per_user = Column(Numeric(10,6))
    bounce_rate = Column(Numeric(10,6))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class GAEcommerce(Base):
    __tablename__ = "ecommerce"
    __table_args__ = {"schema": "google_analytics"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    item_id = Column(Text)
    item_name = Column(Text)
    item_category = Column(Text)
    session_default_channel_group = Column(Text)
    ecommerce_purchases = Column(BigInteger)
    purchase_revenue = Column(Numeric(18,6))
    gross_purchase_revenue = Column(Numeric(18,6))
    total_revenue = Column(Numeric(18,6))
    transactions = Column(BigInteger)
    transactions_per_purchaser = Column(Numeric(10,6))
    items_purchased = Column(BigInteger)
    items_viewed = Column(BigInteger)
    item_view_events = Column(BigInteger)
    items_added_to_cart = Column(BigInteger)
    add_to_carts = Column(BigInteger)
    items_checked_out = Column(BigInteger)
    checkouts = Column(BigInteger)
    refund_amount = Column(Numeric(18,6))
    tax_amount = Column(Numeric(18,6))
    shipping_amount = Column(Numeric(18,6))
    item_revenue = Column(Numeric(18,6))
    item_discount_amount = Column(Numeric(18,6))
    gross_item_revenue = Column(Numeric(18,6))
    average_purchase_revenue = Column(Numeric(18,6))
    average_purchase_revenue_per_paying_user = Column(Numeric(18,6))
    average_purchase_revenue_per_user = Column(Numeric(18,6))
    average_revenue_per_user = Column(Numeric(18,6))
    cart_to_view_rate = Column(Numeric(10,6))
    purchase_to_view_rate = Column(Numeric(10,6))
    purchaser_rate = Column(Numeric(10,6))
    first_time_purchasers = Column(BigInteger)
    first_time_purchaser_rate = Column(Numeric(10,6))
    first_time_purchasers_per_new_user = Column(Numeric(10,6))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class GAAds(Base):
    __tablename__ = "ads"
    __table_args__ = {"schema": "google_analytics"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    ad_unit_name = Column(Text)
    ad_format = Column(Text)
    ad_source_name = Column(Text)
    campaign_name = Column(Text)
    campaign_id = Column(Text)
    session_default_channel_group = Column(Text)
    advertiser_ad_clicks = Column(BigInteger)
    advertiser_ad_impressions = Column(BigInteger)
    advertiser_ad_cost = Column(Numeric(18,6))
    advertiser_ad_cost_per_click = Column(Numeric(18,6))
    advertiser_ad_cost_per_key_event = Column(Numeric(18,6))
    total_ad_revenue = Column(Numeric(18,6))
    return_on_ad_spend = Column(Numeric(10,6))
    publisher_ad_clicks = Column(BigInteger)
    publisher_ad_impressions = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class GAPromotions(Base):
    __tablename__ = "promotions"
    __table_args__ = {"schema": "google_analytics"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    session_default_channel_group = Column(Text)
    promotion_views = Column(BigInteger)
    promotion_clicks = Column(BigInteger)
    item_promotion_click_through_rate = Column(Numeric(10,6))
    items_clicked_in_promotion = Column(BigInteger)
    items_viewed_in_promotion = Column(BigInteger)
    item_list_view_events = Column(BigInteger)
    item_list_click_events = Column(BigInteger)
    item_list_click_through_rate = Column(Numeric(10,6))
    items_clicked_in_list = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
