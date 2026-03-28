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
from app.services.alerts import AlertService

router = APIRouter()
market_service = MarketService()
alert_service = AlertService()


class CreateAccountRequest(BaseModel):
    initial_balance: float = 10000.0
    name: Optional[str] = None


class OrderRequest(BaseModel):
    account_id: str
    symbol: str  # ej: ETH/USDC
    side: str  # buy o sell
    amount_usd: float  # Amount in USD (e.g., 100 means buy $100 worth of crypto)
    order_type: str = "market"
    # Optional SL/TP
    stop_loss_pct: Optional[float] = None  # e.g., 5.0 = 5% stop loss
    take_profit_pct: Optional[float] = None  # e.g., 10.0 = 10% take profit


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


@router.get("/accounts")
async def list_accounts(
    db: AsyncSession = Depends(get_db)
):
    """Listar todas las cuentas de paper trading"""
    result = await db.execute(
        select(PaperAccount).order_by(PaperAccount.created_at.desc())
    )
    accounts = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "created_at": a.created_at,
            "initial_balance": a.initial_balance_usd,
            "current_balance": a.current_balance_usd,
            "is_active": a.is_active
        }
        for a in accounts
    ]


@router.get("/account/{account_id}")
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Obtener estado de cuenta"""
    try:
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
            try:
                current_price = await market_service.get_price(pos.symbol)
                if current_price:
                    pos.current_price = current_price
                    pos.unrealized_pnl = (current_price - pos.entry_price) * pos.amount
                    if pos.side == "sell":
                        pos.unrealized_pnl = -pos.unrealized_pnl
                    total_unrealized_pnl += pos.unrealized_pnl
            except Exception as e:
                print(f"Error getting price for {pos.symbol}: {e}")
            
            positions_data.append({
                "id": pos.id,
                "symbol": pos.symbol,
                "side": pos.side,
                "amount": pos.amount,
                "entry_price": pos.entry_price,
                "current_price": getattr(pos, 'current_price', None),
                "unrealized_pnl": getattr(pos, 'unrealized_pnl', 0)
            })
        
        try:
            await db.commit()
        except Exception as e:
            print(f"Error committing: {e}")
            await db.rollback()
        
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_account: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


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
    
    # Calcular cantidad de crypto basada en USD
    # req.amount_usd = 100 USD, price = 2000 USD/ETH -> crypto_amount = 0.05 ETH
    amount_usd = req.amount_usd
    crypto_amount = amount_usd / price
    fee = amount_usd * 0.001  # 0.1% fee on USD amount
    total_cost = amount_usd + fee
    
    # Verificar fondos suficientes
    if req.side == "buy":
        if account.current_balance_usd < total_cost:
            raise HTTPException(status_code=400, detail=f"Fondos insuficientes. Necesitas ${total_cost:.2f} pero tienes ${account.current_balance_usd:.2f}")
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
        if not position or position.amount < crypto_amount:
            raise HTTPException(status_code=400, detail=f"No tienes suficiente posición para vender. Tienes {position.amount if position else 0:.6f} pero necesitas {crypto_amount:.6f}")
    
    # Crear orden
    metadata = {
        "amount_usd": float(amount_usd),
        "crypto_amount": float(crypto_amount)
    }
    
    # Add SL/TP if provided
    if req.stop_loss_pct:
        metadata["stop_loss_pct"] = req.stop_loss_pct
        metadata["stop_loss_price"] = price * (1 - req.stop_loss_pct / 100)
    
    if req.take_profit_pct:
        metadata["take_profit_pct"] = req.take_profit_pct
        metadata["take_profit_price"] = price * (1 + req.take_profit_pct / 100)
    
    order = PaperOrder(
        id=str(uuid.uuid4()),
        account_id=req.account_id,
        symbol=req.symbol,
        side=req.side,
        order_type=req.order_type,
        amount=crypto_amount,  # Store crypto amount
        price=price,
        fee=fee,
        executed_at=datetime.utcnow(),
        metadata_json=metadata
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
            total_amount = position.amount + crypto_amount
            position.entry_price = (
                (position.entry_price * position.amount) + (price * crypto_amount)
            ) / total_amount
            position.amount = total_amount
        else:
            position = PaperPosition(
                id=str(uuid.uuid4()),
                account_id=req.account_id,
                symbol=req.symbol,
                side="long",
                amount=crypto_amount,
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
            pnl = (price - position.entry_price) * crypto_amount
            order.pnl = pnl
            account.current_balance_usd += (amount_usd - fee)
            
            position.amount -= crypto_amount
            if position.amount <= 0:
                position.is_open = False
    
    db.add(order)
    await db.commit()
    
    # Enviar alerta de orden ejecutada
    await alert_service.send_order_alert(
        symbol=order.symbol,
        side=order.side,
        amount=order.amount,
        price=order.price,
        pnl=order.pnl
    )
    
    return {
        "order_id": order.id,
        "symbol": order.symbol,
        "side": order.side,
        "amount_usd": amount_usd,
        "crypto_amount": crypto_amount,
        "price": order.price,
        "fee": order.fee,
        "pnl": order.pnl,
        "status": "filled",
        "remaining_balance": account.current_balance_usd,
        "stop_loss": metadata.get("stop_loss_price"),
        "take_profit": metadata.get("take_profit_price"),
        "stop_loss_pct": metadata.get("stop_loss_pct"),
        "take_profit_pct": metadata.get("take_profit_pct")
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
