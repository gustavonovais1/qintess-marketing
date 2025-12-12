from fastapi import APIRouter
from .endpoints.instagram import router as instagram_router
from .endpoints.linkedin import router as linkedin_router

router = APIRouter()
router.include_router(instagram_router, prefix="/ig", tags=["Instagram"])
router.include_router(linkedin_router, prefix="/ll", tags=["LinkedIn"])
