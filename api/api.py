from fastapi import APIRouter
from .endpoints.google_analytics import router as google_analytics_router
from .endpoints.rd_station import router as rd_station_router
from .endpoints.instagram import router as instagram_router
from .endpoints.linkedin import router as linkedin_router
from .endpoints.user import router as user_router

router = APIRouter()
router.include_router(user_router, prefix="/user", tags=["User"])
router.include_router(instagram_router, prefix="/ig", tags=["Instagram"])
router.include_router(linkedin_router, prefix="/ll", tags=["LinkedIn"])
router.include_router(google_analytics_router, prefix="/ga", tags=["Google Analytics"])
router.include_router(rd_station_router, prefix="/rd", tags=["RD Station"])