"""Open Trader Backend - FastAPI Application"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import (
    paper_trading, market_data, strategies, health, 
    dashboard, advanced_orders, agent, websocket, export, journal, webhook, user_config
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Create data directory if not exists
    os.makedirs("data", exist_ok=True)
    
    # Initialize database
    await init_db()
    
    # Start SL/TP Monitor Service
    from app.services.sltp_monitor import get_sltp_monitor
    sltp_monitor = get_sltp_monitor()
    await sltp_monitor.start()
    
    # Log available routes for debugging
    print("🚀 Open Trader v0.5.0 iniciado")
    print("🎯 SL/TP Monitor started")
    print("📡 Routes loaded:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            methods = ','.join(route.methods)
            print(f"  {methods} {route.path}")
    
    yield
    
    # Stop SL/TP Monitor
    await sltp_monitor.stop()
    
    print("👋 Open Trader detenido")


app = FastAPI(
    title="Open Trader API",
    description="Sistema de trading algorítmico con paper trading, Multi-DEX y Agente AI",
    version="0.5.0",
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
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(export.router, prefix="/export", tags=["Export"])
app.include_router(journal.router, prefix="/journal", tags=["Trading Journal"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])
app.include_router(user_config.router, prefix="/user", tags=["User Config"])


@app.get("/")
async def root():
    return {
        "name": "Open Trader",
        "version": "0.5.0",
        "status": "running",
        "mode": "paper_trading",
        "features": [
            "multi-dex", "advanced-orders", "realtime-charts", 
            "multi-provider", "ai-agent", "i18n", "postgresql",
            "websocket", "export", "trading-journal", "webhooks"
        ],
        "docs": "/docs" if os.getenv("DEBUG", "false").lower() == "true" else None,
        "dashboard": "/"
    }


@app.get("/version")
async def version():
    """Get current API version"""
    return {
        "version": "0.5.0",
        "release_date": "2026-03-28",
        "features": [
            "paper-trading", "multi-dex", "ai-agent", "auto-trading", 
            "i18n", "postgresql", "websocket-realtime", "export-csv-json",
            "trading-journal", "webhook-signals"
        ],
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
