from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from services.google_analytics import (
    engagement_report,
    ecommerce_items_report,
    ecommerce_revenue_report,
    ecommerce_funnel_report,
    events_report,
    users_report,
    content_report,
    ads_report,
    promotions_report,
)
from core.auth import get_current_user_oauth
from models.models_user import User

router = APIRouter()

DEFAULT_START = (date.today() - timedelta(days=30)).isoformat()
DEFAULT_END = date.today().isoformat()

@router.get("/analytics/engagement")
def analytics_engagement(
    metrics: str = Query("engagedSessions,engagementRate,averageSessionDuration,userEngagementDuration,eventsPerSession,sessionKeyEventRate,userKeyEventRate,scrolledUsers"),
    dimensions: str = Query("date,deviceCategory,country"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return engagement_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/users")
def analytics_users(
    metrics: str = Query("activeUsers,newUsers,totalUsers,active1DayUsers,active7DayUsers,active28DayUsers,dauPerMau,dauPerWau,wauPerMau"),
    dimensions: str = Query("date,country,deviceCategory"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return users_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/events")
def analytics_events(
    metrics: str = Query("eventCount,eventCountPerUser,eventValue,keyEvents"),
    dimensions: str = Query("date,eventName,pagePath"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return events_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/content")
def analytics_content(
    metrics: str = Query("screenPageViews,screenPageViewsPerSession,screenPageViewsPerUser,bounceRate"),
    dimensions: str = Query("date,pageTitle,pagePath"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return content_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/ads")
def analytics_ads(
    metrics: str = Query("advertiserAdClicks,advertiserAdImpressions,advertiserAdCost,advertiserAdCostPerClick"),
    dimensions: str = Query("date,campaignName,campaignId"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return ads_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/promotions")
def analytics_promotions(
    metrics: str = Query("promotionViews,promotionClicks,itemPromotionClickThroughRate,itemsClickedInPromotion,itemsViewedInPromotion,itemListViewEvents,itemListClickEvents,itemListClickThroughRate,itemsClickedInList"),
    dimensions: str = Query("date,sessionDefaultChannelGroup"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return promotions_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/ecommerce/items")
def analytics_ecommerce_items(
    metrics: str = Query("itemsPurchased,itemsViewed,itemsAddedToCart,itemsCheckedOut,itemRevenue,itemDiscountAmount,grossItemRevenue"),
    dimensions: str = Query("date,itemId,itemName,itemCategory"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return ecommerce_items_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/ecommerce/revenue")
def analytics_ecommerce_revenue(
    metrics: str = Query("ecommercePurchases,purchaseRevenue,grossPurchaseRevenue,totalRevenue,transactions,transactionsPerPurchaser,averagePurchaseRevenue,averagePurchaseRevenuePerPayingUser,averagePurchaseRevenuePerUser,averageRevenuePerUser,purchaserRate,firstTimePurchasers,firstTimePurchaserRate,firstTimePurchasersPerNewUser"),
    dimensions: str = Query("date,sessionDefaultChannelGroup"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return ecommerce_revenue_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/ecommerce/funnel")
def analytics_ecommerce_funnel(
    metrics: str = Query("addToCarts,checkouts,ecommercePurchases,cartToViewRate,purchaseToViewRate"),
    dimensions: str = Query("date,sessionDefaultChannelGroup"),
    start_date: str = Query(DEFAULT_START),
    end_date: str = Query(DEFAULT_END),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_oauth),
):
    try:
        return ecommerce_funnel_report(metrics, dimensions, start_date, end_date, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
