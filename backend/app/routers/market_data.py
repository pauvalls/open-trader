"""Market data endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.market import MarketService

router = APIRouter()
market_service = MarketService()


@router.get("/price/{symbol}")
async def get_price(symbol: str):
    """Obtener precio actual de un par (ej: ETH/USDC)"""
    price = await market_service.get_price(symbol)
    if price is None:
        raise HTTPException(status_code=404, detail=f"Símbolo no encontrado: {symbol}")
    
    return {
        "symbol": symbol,
        "price": price,
        "timestamp": market_service.last_update
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
    """
    klines = await market_service.get_klines(symbol, timeframe, limit)
    if klines is None:
        raise HTTPException(status_code=404, detail=f"No se pudieron obtener datos para {symbol}")
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": klines
    }


@router.get("/tickers")
async def get_tickers():
    """Lista de pares disponibles"""
    tickers = await market_service.get_available_tickers()
    return {"tickers": tickers}
