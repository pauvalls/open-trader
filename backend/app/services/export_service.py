"""
Export service for trading data
"""

import csv
import json
import io
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, PaperOrder, PaperPosition, PaperAccount


class ExportService:
    """Service for exporting trading data"""
    
    async def export_trades_csv(self, account_id: str) -> str:
        """Export trades to CSV format"""
        async with get_db() as db:
            result = await db.execute(
                select(PaperOrder)
                .where(PaperOrder.account_id == account_id)
                .order_by(PaperOrder.created_at.desc())
            )
            orders = result.scalars().all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'ID', 'Symbol', 'Side', 'Type', 'Amount', 'Price', 
                'Fee', 'Total', 'PnL', 'Status', 'Created At', 'Executed At'
            ])
            
            # Data
            for order in orders:
                writer.writerow([
                    order.id,
                    order.symbol,
                    order.side,
                    order.order_type,
                    order.amount,
                    order.price,
                    order.fee,
                    order.amount * order.price + order.fee,
                    order.pnl or '',
                    order.status,
                    order.created_at.isoformat() if order.created_at else '',
                    order.executed_at.isoformat() if order.executed_at else ''
                ])
            
            return output.getvalue()
    
    async def export_trades_json(self, account_id: str) -> List[Dict]:
        """Export trades to JSON format"""
        async with get_db() as db:
            result = await db.execute(
                select(PaperOrder)
                .where(PaperOrder.account_id == account_id)
                .order_by(PaperOrder.created_at.desc())
            )
            orders = result.scalars().all()
            
            return [
                {
                    'id': order.id,
                    'symbol': order.symbol,
                    'side': order.side,
                    'order_type': order.order_type,
                    'amount': order.amount,
                    'price': order.price,
                    'fee': order.fee,
                    'total': order.amount * order.price + order.fee,
                    'pnl': order.pnl,
                    'status': order.status,
                    'metadata': order.metadata_json,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'executed_at': order.executed_at.isoformat() if order.executed_at else None
                }
                for order in orders
            ]
    
    async def export_positions_json(self, account_id: str) -> List[Dict]:
        """Export positions to JSON"""
        async with get_db() as db:
            result = await db.execute(
                select(PaperPosition)
                .where(PaperPosition.account_id == account_id)
                .order_by(PaperPosition.created_at.desc())
            )
            positions = result.scalars().all()
            
            return [
                {
                    'id': pos.id,
                    'symbol': pos.symbol,
                    'side': pos.side,
                    'amount': pos.amount,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'is_open': pos.is_open,
                    'opened_at': pos.opened_at.isoformat() if pos.opened_at else None,
                    'created_at': pos.created_at.isoformat() if pos.created_at else None
                }
                for pos in positions
            ]
    
    async def export_full_report(self, account_id: str) -> Dict[str, Any]:
        """Export full trading report with analytics"""
        async with get_db() as db:
            # Get account info
            account_result = await db.execute(
                select(PaperAccount).where(PaperAccount.id == account_id)
            )
            account = account_result.scalar_one_or_none()
            
            if not account:
                return {'error': 'Account not found'}
            
            # Get all orders
            orders_result = await db.execute(
                select(PaperOrder)
                .where(PaperOrder.account_id == account_id)
                .order_by(PaperOrder.created_at.desc())
            )
            orders = orders_result.scalars().all()
            
            # Get open positions
            positions_result = await db.execute(
                select(PaperPosition)
                .where(
                    PaperPosition.account_id == account_id,
                    PaperPosition.is_open == True
                )
            )
            positions = positions_result.scalars().all()
            
            # Calculate stats
            total_trades = len(orders)
            winning_trades = [o for o in orders if o.pnl and o.pnl > 0]
            losing_trades = [o for o in orders if o.pnl and o.pnl < 0]
            
            total_pnl = sum(o.pnl for o in orders if o.pnl) or 0
            win_rate = len(winning_trades) / len([o for o in orders if o.pnl]) * 100 if orders else 0
            
            avg_win = sum(o.pnl for o in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(o.pnl for o in losing_trades) / len(losing_trades) if losing_trades else 0
            
            profit_factor = abs(sum(o.pnl for o in winning_trades) / sum(o.pnl for o in losing_trades)) if losing_trades and sum(o.pnl for o in losing_trades) != 0 else float('inf')
            
            return {
                'generated_at': datetime.utcnow().isoformat(),
                'account': {
                    'id': account.id,
                    'name': account.name,
                    'initial_balance': float(account.initial_balance),
                    'current_balance': float(account.current_balance_usd),
                    'total_pnl': total_pnl,
                    'roi_percent': (total_pnl / float(account.initial_balance)) * 100 if account.initial_balance else 0
                },
                'summary': {
                    'total_trades': total_trades,
                    'winning_trades': len(winning_trades),
                    'losing_trades': len(losing_trades),
                    'win_rate_percent': round(win_rate, 2),
                    'total_pnl': round(total_pnl, 2),
                    'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else None,
                    'average_win': round(avg_win, 2),
                    'average_loss': round(avg_loss, 2),
                    'open_positions': len(positions)
                },
                'trades': await self.export_trades_json(account_id),
                'open_positions': await self.export_positions_json(account_id)
            }


# Global instance
export_service = ExportService()
