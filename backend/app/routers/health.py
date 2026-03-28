"""Health check endpoint"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }
