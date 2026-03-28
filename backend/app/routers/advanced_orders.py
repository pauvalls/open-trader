"""Advanced Orders Router - Órdenes con stop-loss, limit, trailing stop"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from decimal import Decimal

from app.services.trading_service import (
    trading_service, OrderSide, OrderType, OrderStatus
)
from app.services.market import MarketService

router = APIRouter()
market_service = MarketService()


class MarketOrderRequest(BaseModel):
    account_id: str
    symbol: str = Field(..., example="ETH/USDT")
    side: Literal["buy", "sell"]
    amount: float = Field(..., gt=0, example=0.5)
    dex_id: str = Field(default="uniswap-arbitrum", 
                       example="uniswap-arbitrum")


class LimitOrderRequest(BaseModel):
    account_id: str
    symbol: str
    side: Literal["buy", "sell"]
    amount: float = Field(..., gt=0)
    price: float = Field(..., gt=0, description="Precio límite de ejecución")
    dex_id: str = Field(default="uniswap-arbitrum")
    expires_hours: Optional[int] = Field(default=None, description="Expira en N horas")


class StopLossRequest(BaseModel):
    account_id: str
    symbol: str
    side: Literal["buy", "sell"]
    amount: float = Field(..., gt=0)
    stop_price: float = Field(..., gt=0, description="Precio que activa el stop")
    dex_id: str = Field(default="uniswap-arbitrum")


class TrailingStopRequest(BaseModel):
    account_id: str
    symbol: str
    side: Literal["buy", "sell"]
    amount: float = Field(..., gt=0)
    trailing_percent: float = Field(..., gt=0, le=50, 
                                    description="Porcentaje de distancia del trailing stop",
                                    example=5.0)
    dex_id: str = Field(default="uniswap-arbitrum")


class BracketOrderRequest(BaseModel):
    account_id: str
    symbol: str
    side: Literal["buy", "sell"]
    amount: float = Field(..., gt=0)
    entry_price: Optional[float] = Field(default=None, 
                                         description="Precio de entrada (null para market)")
    stop_loss_price: float = Field(..., gt=0, description="Precio del stop loss")
    take_profit_price: float = Field(..., gt=0, description="Precio del take profit")
    dex_id: str = Field(default="uniswap-arbitrum")


@router.post("/market", response_model=dict)
async def create_market_order(req: MarketOrderRequest):
    """Crear orden de mercado (ejecución inmediata)"""
    order = await trading_service.create_market_order(
        account_id=req.account_id,
        symbol=req.symbol,
        side=OrderSide(req.side),
        amount=Decimal(str(req.amount)),
        dex_id=req.dex_id
    )
    return {
        "order_id": order.id,
        "type": "market",
        "status": order.status.value,
        "message": "Orden de mercado creada y ejecutada"
    }


@router.post("/limit", response_model=dict)
async def create_limit_order(req: LimitOrderRequest):
    """
    Crear orden limit.
    
    - BUY: Ejecuta cuando el precio baja al límite o menos
    - SELL: Ejecuta cuando el precio sube al límite o más
    """
    order = await trading_service.create_limit_order(
        account_id=req.account_id,
        symbol=req.symbol,
        side=OrderSide(req.side),
        amount=Decimal(str(req.amount)),
        price=Decimal(str(req.price)),
        dex_id=req.dex_id,
        expires_hours=req.expires_hours
    )
    return {
        "order_id": order.id,
        "type": "limit",
        "status": order.status.value,
        "price": req.price,
        "message": f"Orden limit {req.side} activa a ${req.price}"
    }


@router.post("/stop-loss", response_model=dict)
async def create_stop_loss(req: StopLossRequest):
    """
    Crear orden de stop loss.
    
    Ejemplos:
    - Compraste ETH a $2000, quieres salir si baja a $1800:
      side=SELL, stop_price=1800
    - Vendiste ETH a $2000 (short), quieres salir si sube a $2200:
      side=BUY, stop_price=2200
    """
    order = await trading_service.create_stop_loss(
        account_id=req.account_id,
        symbol=req.symbol,
        side=OrderSide(req.side),
        amount=Decimal(str(req.amount)),
        stop_price=Decimal(str(req.stop_price)),
        dex_id=req.dex_id
    )
    return {
        "order_id": order.id,
        "type": "stop_loss",
        "status": order.status.value,
        "stop_price": req.stop_price,
        "message": f"Stop loss activo a ${req.stop_price}"
    }


@router.post("/trailing-stop", response_model=dict)
async def create_trailing_stop(req: TrailingStopRequest):
    """
    Crear trailing stop loss.
    
    El stop se mueve con el precio favorable, manteniendo una distancia fija.
    
    Ejemplo (trailing 5% en long):
    - Compras ETH a $2000
    - ETH sube a $2200 → stop se mueve a $2090
    - ETH sube a $2400 → stop se mueve a $2280
    - ETH baja a $2300 → no se activa (stop en $2280)
    - ETH baja a $2270 → se activa y vende
    """
    order = await trading_service.create_trailing_stop(
        account_id=req.account_id,
        symbol=req.symbol,
        side=OrderSide(req.side),
        amount=Decimal(str(req.amount)),
        trailing_percent=Decimal(str(req.trailing_percent)),
        dex_id=req.dex_id
    )
    return {
        "order_id": order.id,
        "type": "trailing_stop",
        "status": order.status.value,
        "trailing_percent": req.trailing_percent,
        "message": f"Trailing stop del {req.trailing_percent}% activo"
    }


@router.post("/bracket", response_model=dict)
async def create_bracket_order(req: BracketOrderRequest):
    """
    Crear orden bracket completa: Entry + Stop Loss + Take Profit.
    
    Cuando se ejecuta la entrada, se activan SL y TP en modo OCO
    (One-Cancels-Other):
    - Si se activa el Stop Loss, el Take Profit se cancela
    - Si se activa el Take Profit, el Stop Loss se cancela
    
    Ejemplo:
    - Entry: BUY ETH @ $2000 (o market)
    - Stop Loss: SELL ETH @ $1800 (limitar pérdida a 10%)
    - Take Profit: SELL ETH @ $2400 (ganancia objetivo 20%)
    """
    bracket = await trading_service.create_bracket_order(
        account_id=req.account_id,
        symbol=req.symbol,
        side=OrderSide(req.side),
        amount=Decimal(str(req.amount)),
        entry_price=Decimal(str(req.entry_price)) if req.entry_price else None,
        stop_loss_price=Decimal(str(req.stop_loss_price)),
        take_profit_price=Decimal(str(req.take_profit_price)),
        dex_id=req.dex_id
    )
    return {
        "bracket_id": bracket.entry_order.id,
        "entry_order_id": bracket.entry_order.id,
        "stop_loss_order_id": bracket.stop_loss_order.id,
        "take_profit_order_id": bracket.take_profit_order.id,
        "entry_type": "limit" if req.entry_price else "market",
        "entry_price": req.entry_price,
        "stop_loss": req.stop_loss_price,
        "take_profit": req.take_profit_price,
        "message": "Orden bracket creada (Entry + SL + TP con OCO)"
    }


@router.delete("/{order_id}")
async def cancel_order(order_id: str):
    """Cancelar una orden pendiente"""
    success = await trading_service.cancel_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Orden no encontrada o no cancelable")
    return {"message": "Orden cancelada", "order_id": order_id}


@router.get("/open/{account_id}")
async def get_open_orders(account_id: str):
    """Obtener órdenes abiertas de una cuenta"""
    orders = trading_service.get_open_orders(account_id)
    return {
        "orders": [
            {
                "id": o.id,
                "symbol": o.symbol,
                "side": o.side.value,
                "type": o.order_type.value,
                "amount": float(o.amount),
                "status": o.status.value,
                "entry_price": float(o.entry_price) if o.entry_price else None,
                "stop_price": float(o.stop_price) if o.stop_price else None,
                "trailing_percent": float(o.trailing_percent) if o.trailing_percent else None,
                "created_at": o.created_at.isoformat()
            }
            for o in orders
        ]
    }


@router.get("/history/{account_id}")
async def get_order_history(account_id: str):
    """Obtener historial de órdenes ejecutadas/canceladas"""
    orders = trading_service.get_order_history(account_id)
    return {
        "orders": [
            {
                "id": o.id,
                "symbol": o.symbol,
                "side": o.side.value,
                "type": o.order_type.value,
                "amount": float(o.amount),
                "status": o.status.value,
                "filled_price": float(o.filled_price) if o.filled_price else None,
                "created_at": o.created_at.isoformat()
            }
            for o in orders
        ]
    }


@router.get("/dexes")
async def list_dexes():
    """Listar todos los DEXs disponibles"""
    from app.services.dex_service import list_available_dexes
    return {"dexes": list_available_dexes()}
