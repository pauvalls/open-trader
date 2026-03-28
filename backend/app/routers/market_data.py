"""Market data endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.market_multi import get_market_service

router = APIRouter()


@router.get("/price/{symbol}")
async def get_price(symbol: str):
    """Obtener precio actual de un par (ej: ETH/USDC)"""
    service = get_market_service()
    price = await service.get_price(symbol)
    
    if price is None:
        raise HTTPException(status_code=404, detail=f"Símbolo no encontrado: {symbol}")
    
    return {
        "symbol": symbol,
        "price": price,
        "timestamp": service.last_update,
        "provider": service.get_current_provider()
    }


@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100
):
    """
    Obtener velas históricas (OHLCV)
    
    Timeframes: 1m, 5m, 15m, 1h, 4h, 1d
    
    Usa múltiples providers con fallback automático:
    Binance → Bybit → Kraken → KuCoin
    """
    service = get_market_service()
    klines = await service.get_klines(symbol, timeframe, limit)
    
    if klines is None:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudieron obtener datos para {symbol}. Todos los providers fallaron."
        )
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "provider": service.get_current_provider(),
        "count": len(klines),
        "data": klines
    }


@router.get("/tickers")
async def get_tickers():
    """Lista de pares disponibles"""
    service = get_market_service()
    tickers = await service.get_available_tickers()
    return {"tickers": tickers}


@router.get("/status")
async def get_status():
    """Estado del servicio de datos y provider activo"""
    service = get_market_service()
    
    # Test rápido para ver qué provider responde
    test_price = await service.get_price("ETH/USDT")
    
    return {
        "status": "ok" if test_price else "degraded",
        "active_provider": service.get_current_provider(),
        "available_providers": ["binance", "bybit", "kraken", "kucoin"],
        "last_update": service.last_update,
        "test_price_eth": test_price
    }
