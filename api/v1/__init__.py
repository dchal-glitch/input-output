from fastapi import APIRouter
from api.v1 import io

api_router = APIRouter(prefix="/api/v1")

# Include all route modules
api_router.include_router(io.router)
