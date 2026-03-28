"""Open Trader Backend - FastAPI Application"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import paper_trading, market_data, strategies, health, dashboard, advanced_orders, agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Create data directory if not exists
    os.makedirs("data", exist_ok=True)
    
    # Initialize database
    await init_db()
    
    # Log available routes for debugging
    print("🚀 Open Trader v0.4.0 iniciado")
    print("📡 Routes loaded:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            methods = ','.join(route.methods)
            print(f"  {methods} {route.path}")
    
    yield
    print("👋 Open Trader detenido")


app = FastAPI(
    title="Open Trader API",
    description="Sistema de trading algorítmico con paper trading, Multi-DEX y Agente AI",
    version="0.4.0",
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
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(paper_trading.router, prefix="/paper", tags=["Paper Trading"])
app.include_router(market_data.router, prefix="/market", tags=["Market Data"])
app.include_router(strategies.router, prefix="/strategies", tags=["Estrategias"])
app.include_router(advanced_orders.router, prefix="/orders", tags=["Órdenes Avanzadas"])
app.include_router(agent.router, tags=["AI Trading Agent"])


@app.get("/")
async def root():
    return {
        "name": "Open Trader",
        "version": "0.4.0",
        "status": "running",
        "mode": "paper_trading",
        "features": ["multi-dex", "advanced-orders", "realtime-charts", "multi-provider", "ai-agent"],
        "docs": "/docs" if os.getenv("DEBUG", "false").lower() == "true" else None,
        "dashboard": "/dashboard/"
    }


@app.get("/version")
async def version():
    """Get current API version"""
    return {
        "version": "0.4.0",
        "release_date": "2026-03-28",
        "features": ["paper-trading", "multi-dex", "ai-agent", "auto-trading"],
        "changelog": "https://github.com/pauvalls/open-trader/blob/main/CHANGELOG.md"
    }


@app.get("/routes")
async def list_routes():
    """Debug: List all available routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name if hasattr(route, 'name') else None
            })
    return {"routes": routes, "count": len(routes)}
