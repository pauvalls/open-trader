"""Paper Trading endpoints"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.database import get_db, PaperAccount, PaperOrder, PaperPosition
from app.services.market import MarketService

router = APIRouter()
market_service = MarketService()


class CreateAccountRequest(BaseModel):
    initial_balance: float = 10000.0
    name: Optional[str] = None


class OrderRequest(BaseModel):
    account_id: str
    symbol: str  # ej: ETH/USDC
    side: str  # buy o sell
    amount: float
    order_type: str = "market"


@router.post("/account")
async def create_account(
    req: CreateAccountRequest,
    db: AsyncSession = Depends(get_db)
):
    """Crear nueva cuenta de paper trading"""
    account = PaperAccount(
        id=str(uuid.uuid4()),
        initial_balance_usd=req.initial_balance,
        current_balance_usd=req.initial_balance,
    )
    db.add(account)
    await db.commit()
    
    return {
        "id": account.id,
        "initial_balance": account.initial_balance_usd,
        "current_balance": account.current_balance_usd,
        "created_at": account.created_at
    }


@router.get("/account/{account_id}")
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Obtener estado de cuenta"""
    result = await db.execute(
        select(PaperAccount).where(PaperAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    # Calcular P&L de posiciones abiertas
    positions_result = await db.execute(
        select(PaperPosition).where(
            PaperPosition.account_id == account_id,
            PaperPosition.is_open == True
        )
    )
    positions = positions_result.scalars().all()
    
    # Actualizar precios actuales
    total_unrealized_pnl = 0.0
    positions_data = []
    
    for pos in positions:
        current_price = await market_service.get_price(pos.symbol)
        if current_price:
            pos.current_price = current_price
            pos.unrealized_pnl = (current_price - pos.entry_price) * pos.amount
            if pos.side == "sell":
                pos.unrealized_pnl = -pos.unrealized_pnl
            total_unrealized_pnl += pos.unrealized_pnl
        
        positions_data.append({
            "id": pos.id,
            "symbol": pos.symbol,
            "side": pos.side,
            "amount": pos.amount,
            "entry_price": pos.entry_price,
            "current_price": pos.current_price,
            "unrealized_pnl": pos.unrealized_pnl
        })
    
    await db.commit()
    
    return {
        "id": account.id,
        "initial_balance": account.initial_balance_usd,
        "current_balance": account.current_balance_usd,
        "total_value": account.current_balance_usd + sum(
            p["amount"] * (p["current_price"] or p["entry_price"]) 
            for p in positions_data
        ),
        "unrealized_pnl": total_unrealized_pnl,
        "open_positions": len(positions),
        "positions": positions_data
    }


@router.post("/order")
async def create_order(
    req: OrderRequest,
    db: AsyncSession = Depends(get_db)
):
    """Ejecutar orden de paper trading"""
    # Verificar cuenta
    result = await db.execute(
        select(PaperAccount).where(PaperAccount.id == req.account_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    # Obtener precio actual
    price = await market_service.get_price(req.symbol)
    if not price:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener precio para {req.symbol}")
    
    # Calcular valor y fee
    order_value = req.amount * price
    fee = order_value * 0.001  # 0.1% fee
    total_cost = order_value + fee
    
    # Verificar fondos suficientes
    if req.side == "buy":
        if account.current_balance_usd < total_cost:
            raise HTTPException(status_code=400, detail="Fondos insuficientes")
        account.current_balance_usd -= total_cost
    else:
        # Verificar que tiene la posición para vender
        pos_result = await db.execute(
            select(PaperPosition).where(
                PaperPosition.account_id == req.account_id,
                PaperPosition.symbol == req.symbol,
                PaperPosition.is_open == True
            )
        )
        position = pos_result.scalar_one_or_none()
        if not position or position.amount < req.amount:
            raise HTTPException(status_code=400, detail="No tienes suficiente posición para vender")
    
    # Crear orden
    order = PaperOrder(
        id=str(uuid.uuid4()),
        account_id=req.account_id,
        symbol=req.symbol,
        side=req.side,
        order_type=req.order_type,
        amount=req.amount,
        price=price,
        fee=fee,
        executed_at=datetime.utcnow()
    )
    
    # Manejar posición
    if req.side == "buy":
        # Buscar posición existente o crear nueva
        pos_result = await db.execute(
            select(PaperPosition).where(
                PaperPosition.account_id == req.account_id,
                PaperPosition.symbol == req.symbol,
                PaperPosition.is_open == True
            )
        )
        position = pos_result.scalar_one_or_none()
        
        if position:
            # Averiguar precio promedio
            total_amount = position.amount + req.amount
            position.entry_price = (
                (position.entry_price * position.amount) + (price * req.amount)
            ) / total_amount
            position.amount = total_amount
        else:
            position = PaperPosition(
                id=str(uuid.uuid4()),
                account_id=req.account_id,
                symbol=req.symbol,
                side="long",
                amount=req.amount,
                entry_price=price
            )
            db.add(position)
    else:
        # Vender - cerrar posición parcial o total
        pos_result = await db.execute(
            select(PaperPosition).where(
                PaperPosition.account_id == req.account_id,
                PaperPosition.symbol == req.symbol,
                PaperPosition.is_open == True
            )
        )
        position = pos_result.scalar_one_or_none()
        
        if position:
            # Calcular P&L
            pnl = (price - position.entry_price) * req.amount
            order.pnl = pnl
            account.current_balance_usd += (order_value - fee)
            
            position.amount -= req.amount
            if position.amount <= 0:
                position.is_open = False
    
    db.add(order)
    await db.commit()
    
    return {
        "order_id": order.id,
        "symbol": order.symbol,
        "side": order.side,
        "amount": order.amount,
        "price": order.price,
        "fee": order.fee,
        "pnl": order.pnl,
        "status": "filled",
        "remaining_balance": account.current_balance_usd
    }


@router.get("/orders/{account_id}")
async def get_orders(
    account_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Obtener historial de órdenes"""
    result = await db.execute(
        select(PaperOrder)
        .where(PaperOrder.account_id == account_id)
        .order_by(desc(PaperOrder.created_at))
        .limit(limit)
    )
    orders = result.scalars().all()
    
    return [
        {
            "id": o.id,
            "symbol": o.symbol,
            "side": o.side,
            "amount": o.amount,
            "price": o.price,
            "fee": o.fee,
            "pnl": o.pnl,
            "created_at": o.created_at
        }
        for o in orders
    ]
