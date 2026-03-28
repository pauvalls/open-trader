"""Strategies endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import pandas as pd

from app.services.market import MarketService
from app.services.alerts import AlertService
from app.strategies.rsi_strategy import RSIStrategy
from app.strategies.macd_strategy import MACDStrategy
from app.strategies.bollinger_strategy import BollingerStrategy

router = APIRouter()
market_service = MarketService()
alert_service = AlertService()


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
        "description": "Señales basadas en cruce de MACD y línea de señal",
        "params": {
            "fast": 12,
            "slow": 26,
            "signal": 9
        }
    },
    "bollinger": {
        "name": "Bollinger Bands",
        "description": "Trading con bandas de Bollinger - compra en banda inferior, venta en superior",
        "params": {
            "period": 20,
            "std_dev": 2.0,
            "use_confirmation": True
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
    elif strategy_name == "macd":
        strategy = MACDStrategy(req.strategy_params)
        results = strategy.backtest(df, req.initial_balance)
    elif strategy_name == "bollinger":
        strategy = BollingerStrategy(req.strategy_params)
        results = strategy.backtest(df, req.initial_balance)
    else:
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
        extra_info = {"rsi": signal.get("rsi")}
    elif strategy_name == "macd":
        strategy = MACDStrategy()
        signal = strategy.get_signal(df)
        extra_info = {
            "macd": signal.get("macd"),
            "signal": signal.get("signal"),
            "histogram": signal.get("histogram")
        }
    elif strategy_name == "bollinger":
        strategy = BollingerStrategy()
        signal = strategy.get_signal(df)
        extra_info = {
            "sma": signal.get("sma"),
            "upper": signal.get("upper"),
            "lower": signal.get("lower"),
            "percent_b": signal.get("percent_b")
        }
    else:
        return {"error": "Estrategia no implementada"}
    
    # Enviar alerta si hay señal de compra o venta
    if signal["action"] in ["buy", "sell"]:
        await alert_service.send_signal_alert(
            strategy=strategy_name.upper(),
            symbol=symbol,
            action=signal["action"],
            price=signal["price"],
            extra_info=extra_info
        )
    
    return {
        "symbol": symbol,
        "strategy": strategy_name,
        "signal": signal["action"],
        "price": signal.get("price"),
        "timestamp": signal.get("timestamp"),
        "indicators": extra_info
    }


@router.post("/scan")
async def scan_all_strategies(symbol: str, timeframe: str = "1h"):
    """Escanea todas las estrategias y devuelve consenso"""
    
    klines = await market_service.get_klines(symbol, timeframe, limit=100)
    if not klines:
        raise HTTPException(status_code=400, detail="No se pudieron obtener datos")
    
    df = pd.DataFrame(klines)
    signals = {}
    
    # RSI
    rsi_strategy = RSIStrategy()
    rsi_signal = rsi_strategy.get_signal(df)
    signals["rsi"] = rsi_signal["action"]
    
    # MACD
    macd_strategy = MACDStrategy()
    macd_signal = macd_strategy.get_signal(df)
    signals["macd"] = macd_signal["action"]
    
    # Bollinger
    bb_strategy = BollingerStrategy()
    bb_signal = bb_strategy.get_signal(df)
    signals["bollinger"] = bb_signal["action"]
    
    # Contar votos
    buy_votes = sum(1 for s in signals.values() if s == "buy")
    sell_votes = sum(1 for s in signals.values() if s == "sell")
    hold_votes = sum(1 for s in signals.values() if s == "hold")
    
    # Consenso
    if buy_votes >= 2:
        consensus = "buy"
    elif sell_votes >= 2:
        consensus = "sell"
    else:
        consensus = "hold"
    
    current_price = df['close'].iloc[-1]
    
    # Enviar alerta si hay consenso fuerte
    if consensus in ["buy", "sell"]:
        await alert_service.send_signal_alert(
            strategy="CONSENSO MULTI-ESTRATEGIA",
            symbol=symbol,
            action=consensus,
            price=current_price,
            extra_info={
                "rsi": signals["rsi"],
                "macd": signals["macd"],
                "bollinger": signals["bollinger"]
            }
        )
    
    return {
        "symbol": symbol,
        "price": current_price,
        "individual_signals": signals,
        "consensus": consensus,
        "buy_votes": buy_votes,
        "sell_votes": sell_votes,
        "hold_votes": hold_votes
    }
