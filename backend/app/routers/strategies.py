"""Strategies endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import pandas as pd

from app.services.market import MarketService
from app.strategies.rsi_strategy import RSIStrategy

router = APIRouter()
market_service = MarketService()


class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_balance: float = 10000.0
    strategy_params: Optional[Dict] = {}


AVAILABLE_STRATEGIES = {
    "rsi": {
        "name": "RSI Strategy",
        "description": "Compra cuando RSI < 30, vende cuando RSI > 70",
        "params": {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70
        }
    },
    "macd": {
        "name": "MACD Strategy", 
        "description": "Señales basadas en cruce de MACD",
        "params": {
            "fast": 12,
            "slow": 26,
            "signal": 9
        }
    },
    "sma_cross": {
        "name": "SMA Cross",
        "description": "Cruce de medias móviles simples",
        "params": {
            "fast_period": 20,
            "slow_period": 50
        }
    }
}


@router.get("/")
async def list_strategies():
    """Listar estrategias disponibles"""
    return AVAILABLE_STRATEGIES


@router.post("/{strategy_name}/backtest")
async def run_backtest(strategy_name: str, req: BacktestRequest):
    """Ejecutar backtest de una estrategia"""
    
    if strategy_name not in AVAILABLE_STRATEGIES:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")
    
    # Obtener datos históricos
    klines = await market_service.get_klines(
        req.symbol, 
        req.timeframe, 
        limit=500
    )
    
    if not klines:
        raise HTTPException(status_code=400, detail="No se pudieron obtener datos históricos")
    
    # Crear DataFrame
    df = pd.DataFrame(klines)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Ejecutar backtest según estrategia
    if strategy_name == "rsi":
        strategy = RSIStrategy(req.strategy_params)
        results = strategy.backtest(df, req.initial_balance)
    else:
        # Placeholder para otras estrategias
        results = {
            "strategy": strategy_name,
            "status": "not_implemented",
            "message": f"Backtest para {strategy_name} aún no implementado"
        }
    
    return results


@router.get("/{strategy_name}/signal")
async def get_signal(strategy_name: str, symbol: str, timeframe: str = "1h"):
    """Obtener señal actual de compra/venta"""
    
    if strategy_name not in AVAILABLE_STRATEGIES:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")
    
    klines = await market_service.get_klines(symbol, timeframe, limit=100)
    if not klines:
        raise HTTPException(status_code=400, detail="No se pudieron obtener datos")
    
    df = pd.DataFrame(klines)
    
    if strategy_name == "rsi":
        strategy = RSIStrategy()
        signal = strategy.get_signal(df)
        return {
            "symbol": symbol,
            "strategy": strategy_name,
            "signal": signal["action"],  # buy, sell, hold
            "rsi": signal.get("rsi"),
            "price": signal.get("price"),
            "timestamp": signal.get("timestamp")
        }
    
    return {"error": "Estrategia no implementada para señales en tiempo real"}
