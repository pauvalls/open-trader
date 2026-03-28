"""
SL/TP Monitor Service

Background service to monitor open positions and automatically close
them when Stop Loss or Take Profit levels are reached.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, PaperPosition, PaperOrder, PaperAccount, async_session
from app.services.market_multi import MultiMarketService
from app.services.alerts import AlertService

market_service = MultiMarketService()
alert_service = AlertService()


class SLTPMonitorService:
    """Service to monitor and execute SL/TP automatically"""
    
    def __init__(self):
        self._running = False
        self._task = None
        self._check_interval = 30  # Check every 30 seconds
    
    async def start(self):
        """Start the monitoring loop"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        print("🎯 SL/TP Monitor started")
    
    async def stop(self):
        """Stop the monitoring loop"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("🛑 SL/TP Monitor stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                await self._check_positions()
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                print(f"❌ SL/TP Monitor error: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def _check_positions(self):
        """Check all open positions for SL/TP triggers"""
        async with async_session() as db:
            # Get all open positions with SL/TP set
            result = await db.execute(
                select(PaperPosition).where(
                    PaperPosition.is_open == True,
                    PaperPosition.stop_loss_price.isnot(None) | PaperPosition.take_profit_price.isnot(None)
                )
            )
            positions = result.scalars().all()
            
            for position in positions:
                await self._check_single_position(position, db)
    
    async def _check_single_position(self, position: PaperPosition, db: AsyncSession):
        """Check if a single position should be closed due to SL/TP"""
        try:
            # Get current price
            ticker = await market_service.get_ticker(position.symbol)
            current_price = ticker.get('last', 0)
            
            if current_price <= 0:
                return
            
            # Update current price in position
            position.current_price = current_price
            
            # Check SL/TP conditions
            trigger_reason = None
            trigger_price = None
            
            if position.side == 'long':
                # For long positions
                if position.stop_loss_price and current_price <= position.stop_loss_price:
                    trigger_reason = 'stop_loss'
                    trigger_price = position.stop_loss_price
                elif position.take_profit_price and current_price >= position.take_profit_price:
                    trigger_reason = 'take_profit'
                    trigger_price = position.take_profit_price
            else:
                # For short positions (if implemented in future)
                if position.stop_loss_price and current_price >= position.stop_loss_price:
                    trigger_reason = 'stop_loss'
                    trigger_price = position.stop_loss_price
                elif position.take_profit_price and current_price <= position.take_profit_price:
                    trigger_reason = 'take_profit'
                    trigger_price = position.take_profit_price
            
            if trigger_reason:
                await self._close_position(position, current_price, trigger_reason, db)
                
        except Exception as e:
            print(f"❌ Error checking position {position.id}: {e}")
    
    async def _close_position(self, position: PaperPosition, current_price: float, 
                              trigger_reason: str, db: AsyncSession):
        """Close a position due to SL/TP trigger"""
        try:
            # Get account
            result = await db.execute(
                select(PaperAccount).where(PaperAccount.id == position.account_id)
            )
            account = result.scalar_one_or_none()
            
            if not account:
                return
            
            # Calculate PnL
            entry_price = Decimal(str(position.entry_price))
            exit_price = Decimal(str(current_price))
            amount = Decimal(str(position.amount))
            
            pnl = (exit_price - entry_price) * amount
            if position.side == 'short':
                pnl = -pnl
            
            # Calculate fee
            position_value_usd = float(exit_price * amount)
            fee = Decimal(str(position_value_usd * 0.001))  # 0.1% fee
            
            # Update account balance
            receive_usd = position_value_usd - float(fee)
            account.current_balance_usd += Decimal(str(receive_usd))
            
            # Mark position as closed
            position.is_open = False
            position.current_price = current_price
            position.unrealized_pnl = float(pnl)
            position.sl_tp_triggered = trigger_reason
            position.sl_tp_triggered_at = datetime.utcnow()
            
            # Create closing order
            order = PaperOrder(
                id=str(uuid.uuid4()),
                account_id=position.account_id,
                symbol=position.symbol,
                side='sell',
                order_type='market',
                amount=position.amount,
                price=current_price,
                fee=float(fee),
                status='filled',
                pnl=float(pnl),
                executed_at=datetime.utcnow(),
                metadata_json={
                    'type': 'sl_tp_close',
                    'trigger': trigger_reason,
                    'position_id': position.id,
                    'entry_price': position.entry_price,
                    'stop_loss_price': position.stop_loss_price,
                    'take_profit_price': position.take_profit_price,
                    'position_value_usd': position_value_usd
                }
            )
            db.add(order)
            
            await db.commit()
            
            # Send alert
            emoji = '🔴' if trigger_reason == 'stop_loss' else '🟢'
            action_text = 'STOP LOSS' if trigger_reason == 'stop_loss' else 'TAKE PROFIT'
            alert_msg = (
                f"{emoji} {action_text} TRIGGERED\n"
                f"Symbol: {position.symbol}\n"
                f"Exit Price: ${current_price:.2f}\n"
                f"PnL: ${float(pnl):+.2f}\n"
                f"{'🔻 SL' if trigger_reason == 'stop_loss' else '💰 TP'}: ${trigger_price:.2f}"
            )
            await alert_service.send_alert(alert_msg, level='info')
            
            print(f"✅ Position closed via {trigger_reason}: {position.symbol} @ ${current_price:.2f} (PnL: ${float(pnl):+.2f})")
            
        except Exception as e:
            print(f"❌ Error closing position {position.id}: {e}")
            await db.rollback()


# Global instance
_sltp_monitor = None


def get_sltp_monitor() -> SLTPMonitorService:
    """Get or create global SL/TP monitor instance"""
    global _sltp_monitor
    if _sltp_monitor is None:
        _sltp_monitor = SLTPMonitorService()
    return _sltp_monitor
