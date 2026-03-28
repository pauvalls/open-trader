"""
Paper Trading Service

Service layer for paper trading operations.
"""

from typing import Optional, Dict, List, Any
from decimal import Decimal
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db, PaperAccount, PaperOrder, PaperPosition
from app.services.market import MarketService
from app.services.alerts import AlertService

market_service = MarketService()
alert_service = AlertService()


class PaperTradingService:
    """Service for paper trading operations"""
    
    async def create_account(
        self, 
        initial_balance: float = 10000.0,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new paper trading account"""
        async with get_db() as db:
            account = PaperAccount(
                id=str(uuid.uuid4()),
                name=name or f"Account-{uuid.uuid4().hex[:8]}",
                initial_balance=Decimal(str(initial_balance)),
                current_balance=Decimal(str(initial_balance)),
                current_balance_usd=Decimal(str(initial_balance)),
                unrealized_pnl=Decimal("0"),
                total_value=Decimal(str(initial_balance))
            )
            db.add(account)
            await db.commit()
            await db.refresh(account)
            
            return {
                "id": account.id,
                "name": account.name,
                "initial_balance": float(account.initial_balance),
                "current_balance": float(account.current_balance),
                "created_at": account.created_at.isoformat() if account.created_at else None
            }
    
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get account details with positions"""
        async with get_db() as db:
            result = await db.execute(
                select(PaperAccount).where(PaperAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if not account:
                raise ValueError(f"Account {account_id} not found")
            
            # Get positions
            positions_result = await db.execute(
                select(PaperPosition).where(PaperPosition.account_id == account_id)
            )
            positions = positions_result.scalars().all()
            
            # Calculate current values
            total_value = Decimal(str(account.current_balance_usd))
            unrealized_pnl = Decimal("0")
            positions_data = []
            
            for pos in positions:
                # Get current price
                try:
                    ticker = await market_service.get_ticker(pos.symbol)
                    current_price = Decimal(str(ticker.get('last', pos.entry_price)))
                except:
                    current_price = pos.entry_price
                
                position_value = pos.amount * current_price
                pnl = (current_price - pos.entry_price) * pos.amount
                if pos.side == 'short':
                    pnl = -pnl
                
                total_value += position_value
                unrealized_pnl += pnl
                
                positions_data.append({
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "amount": float(pos.amount),
                    "entry_price": float(pos.entry_price),
                    "current_price": float(current_price),
                    "unrealized_pnl": float(pnl),
                    "opened_at": pos.created_at.isoformat() if pos.created_at else None,
                    "stop_loss_price": float(pos.stop_loss_price) if pos.stop_loss_price else None,
                    "take_profit_price": float(pos.take_profit_price) if pos.take_profit_price else None,
                    "stop_loss_pct": pos.stop_loss_pct,
                    "take_profit_pct": pos.take_profit_pct
                })
            
            return {
                "id": account.id,
                "name": account.name,
                "initial_balance": float(account.initial_balance),
                "current_balance": float(account.current_balance),
                "current_balance_usd": float(account.current_balance_usd),
                "unrealized_pnl": float(unrealized_pnl),
                "total_value": float(total_value),
                "open_positions": len(positions),
                "positions": positions_data
            }
    
    async def list_accounts(self) -> List[Dict[str, Any]]:
        """List all paper trading accounts"""
        async with get_db() as db:
            result = await db.execute(select(PaperAccount))
            accounts = result.scalars().all()
            
            return [
                {
                    "id": acc.id,
                    "name": acc.name,
                    "initial_balance": float(acc.initial_balance),
                    "current_balance": float(acc.current_balance),
                    "current_balance_usd": float(acc.current_balance_usd),
                    "open_positions": 0  # Would need to count
                }
                for acc in accounts
            ]
    
    async def create_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        amount_usd: float,
        stop_loss_pct: float = None,
        take_profit_pct: float = None
    ) -> Dict[str, Any]:
        """Create a paper trading order
        
        Args:
            account_id: Account ID
            symbol: Trading pair (e.g., ETH/USDT)
            side: 'buy' or 'sell'
            amount_usd: Amount in USD to trade (e.g., 100 means buy $100 worth of ETH)
            stop_loss_pct: Optional stop loss percentage (e.g., 5.0 for 5%)
            take_profit_pct: Optional take profit percentage (e.g., 10.0 for 10%)
        """
        async with get_db() as db:
            # Get account
            result = await db.execute(
                select(PaperAccount).where(PaperAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if not account:
                raise ValueError("Account not found")
            
            # Get current price
            ticker = await market_service.get_ticker(symbol)
            price = Decimal(str(ticker.get('last', 0)))
            
            if price <= 0:
                raise ValueError(f"Could not get price for {symbol}")
            
            # Convert USD amount to crypto amount
            amount_usd_decimal = Decimal(str(amount_usd))
            crypto_amount = amount_usd_decimal / price  # e.g., $100 / $2000 = 0.05 ETH
            fee = amount_usd_decimal * Decimal("0.001")  # 0.1% fee on USD amount
            
            # Prepare metadata with SL/TP
            metadata = {
                'amount_usd': float(amount_usd_decimal),
                'crypto_amount': float(crypto_amount)
            }
            
            if stop_loss_pct:
                metadata['stop_loss_pct'] = stop_loss_pct
                metadata['stop_loss_price'] = float(price * Decimal(str(1 - stop_loss_pct / 100)))
            
            if take_profit_pct:
                metadata['take_profit_pct'] = take_profit_pct
                metadata['take_profit_price'] = float(price * Decimal(str(1 + take_profit_pct / 100)))
            
            if side == 'buy':
                if account.current_balance_usd < amount_usd_decimal + fee:
                    raise ValueError(f"Insufficient balance. Need ${float(amount_usd_decimal + fee):.2f} but have ${float(account.current_balance_usd):.2f}")
                
                account.current_balance_usd -= (amount_usd_decimal + fee)
                
                # Create position with the calculated crypto amount and SL/TP
                position = PaperPosition(
                    account_id=account_id,
                    symbol=symbol,
                    side='long',
                    amount=crypto_amount,
                    entry_price=price,
                    unrealized_pnl=Decimal("0"),
                    stop_loss_price=Decimal(str(metadata.get('stop_loss_price', 0))) if stop_loss_pct else None,
                    take_profit_price=Decimal(str(metadata.get('take_profit_price', 0))) if take_profit_pct else None,
                    stop_loss_pct=stop_loss_pct,
                    take_profit_pct=take_profit_pct
                )
                db.add(position)
                
            elif side == 'sell':
                # Find position to close
                pos_result = await db.execute(
                    select(PaperPosition).where(
                        PaperPosition.account_id == account_id,
                        PaperPosition.symbol == symbol
                    )
                )
                position = pos_result.scalar_one_or_none()
                
                if not position:
                    raise ValueError(f"No position found for {symbol}")
                
                # Calculate PnL
                pnl = (price - position.entry_price) * position.amount
                if position.side == 'short':
                    pnl = -pnl
                
                # When selling, we receive the USD value minus fee
                receive_usd = amount_usd_decimal - fee
                account.current_balance_usd += receive_usd
                account.unrealized_pnl += pnl
                
                # Remove position
                await db.delete(position)
            
            # Create order record (store both USD and crypto amounts)
            order = PaperOrder(
                account_id=account_id,
                symbol=symbol,
                side=side,
                amount=crypto_amount,  # Amount in crypto
                price=price,
                fee=fee,
                status='filled',
                metadata_json=metadata
            )
            db.add(order)
            await db.commit()
            
            # Send alert
            sl_info = f" SL:{stop_loss_pct}%" if stop_loss_pct else ""
            tp_info = f" TP:{take_profit_pct}%" if take_profit_pct else ""
            await alert_service.send_alert(
                f"📝 Paper Trade: {side.upper()} ${amount_usd} of {symbol} = {float(crypto_amount):.6f} @ ${float(price):.2f}{sl_info}{tp_info}",
                level='info'
            )
            
            return {
                "id": order.id,
                "symbol": symbol,
                "side": side,
                "amount_usd": float(amount_usd),
                "crypto_amount": float(crypto_amount),
                "price": float(price),
                "fee": float(fee),
                "total": float(amount_usd_decimal + fee),
                "status": "filled",
                "stop_loss_price": metadata.get('stop_loss_price'),
                "take_profit_price": metadata.get('take_profit_price'),
                "stop_loss_pct": stop_loss_pct,
                "take_profit_pct": take_profit_pct
            }
