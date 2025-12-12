from fastapi import APIRouter, Query
from services import media_list, get_profile, get_insights_profile, get_insights_posts, exchange_token_service

router = APIRouter()

@router.get("/profile")
def ig_profile(fields: str = Query("id,username,name,profile_picture_url,biography,followers_count,follows_count,media_count,website")):
    return get_profile(fields=fields)

@router.get("/media")
def ig_media(fields: str = Query("id,media_type,timestamp"), limit: int = Query(25, ge=1, le=100), media_type: str | None = None, since: int | str | None = None, until: int | str | None = None):
    """
    fields: id,media_type,timestamp,caption,media_url,thumbnail_url,permalink,children{id,media_type},shortcode
    """
    return media_list(fields=fields, limit=limit, media_type=media_type, since=since, until=until)

@router.get("/insights/profile")
def ig_insights_profile(metric: str = "reach, website_clicks, profile_views, accounts_engaged, total_interactions, likes, comments, shares, saves, replies, follows_and_unfollows, profile_links_taps, views, reposts, content_views", since: int | str | None = None, until: int | str | None = None):
    return get_insights_profile(metric=metric, since=since, until=until)

@router.get("/insights/posts")
def ig_insights_posts(media_id: str = Query(...), metric: str = Query("views,reach,saved,likes,comments,shares,total_interactions,reposts")):
    """
    IMAGE, CAROUSEL_ALBUM:

    views, reach, saved, likes, comments, shares, total_interactions, follows, profile_visits, profile_activity, reposts

    VIDEO:

    views, reach, saved, likes, comments, shares, total_interactions, ig_reels_video_view_total_time, ig_reels_avg_watch_time, reels_skip_rate, reposts, facebook_views, crossposted_views
    """
    return get_insights_posts(media_id=media_id, metric=metric)

@router.get("/oauth/exchange_token")
def oauth_exchange_token(fb_exchange_token: str = Query(...)):
    return exchange_token_service(fb_exchange_token=fb_exchange_token)