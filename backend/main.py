"""Open Trader Backend - FastAPI Application"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import paper_trading, market_data, strategies, health, dashboard, advanced_orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Create data directory if not exists
    os.makedirs("data", exist_ok=True)
    
    # Initialize database
    await init_db()
    print("🚀 Open Trader iniciado")
    yield
    print("👋 Open Trader detenido")


app = FastAPI(
    title="Open Trader API",
    description="Sistema de trading algorítmico con paper trading y Multi-DEX",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("DEBUG", "false").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("DEBUG", "false").lower() == "true" else None
)

# CORS - ajustar en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(paper_trading.router, prefix="/paper", tags=["Paper Trading"])
app.include_router(market_data.router, prefix="/market", tags=["Market Data"])
app.include_router(strategies.router, prefix="/strategies", tags=["Estrategias"])
app.include_router(advanced_orders.router, prefix="/orders", tags=["Órdenes Avanzadas"])


@app.get("/")
async def root():
    return {
        "name": "Open Trader",
        "version": "0.3.0",
        "status": "running",
        "mode": "paper_trading",
        "features": ["multi-dex", "advanced-orders", "realtime-charts"],
        "docs": "/docs" if os.getenv("DEBUG", "false").lower() == "true" else None,
        "dashboard": "/dashboard/"
    }


@app.get("/version")
async def version():
    """Get current API version"""
    return {
        "version": "0.2.0",
        "release_date": "2024-03-28",
        "changelog": "https://github.com/pauvalls/open-trader/blob/main/CHANGELOG.md"
    }
