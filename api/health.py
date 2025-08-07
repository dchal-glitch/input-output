from datetime import datetime
from fastapi import APIRouter, status
from schemas.schemas import HealthCheck, Message
from core.config import get_settings

settings = get_settings()
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version
    )


@router.get("/", response_model=Message)
async def root():
    """Root endpoint"""
    return Message(message=f"Welcome to {settings.app_name} v{settings.app_version}")
