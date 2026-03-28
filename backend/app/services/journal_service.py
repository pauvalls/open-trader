"""
Trading Journal - Notes and reflections on trades
"""

from sqlalchemy import select
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from app.database import get_db, TradeJournal


class JournalService:
    """Service for managing trade journals"""
    
    async def create_entry(
        self,
        order_id: str,
        account_id: str,
        notes: str = None,
        emotions: str = None,
        mistakes: str = None,
        lessons: str = None,
        strategy_rating: float = None,
        tags: str = None
    ) -> Dict[str, Any]:
        """Create a new journal entry for a trade"""
        async with get_db() as db:
            entry = TradeJournal(
                order_id=order_id,
                account_id=account_id,
                notes=notes,
                emotions=emotions,
                mistakes=mistakes,
                lessons=lessons,
                strategy_rating=strategy_rating,
                tags=tags
            )
            db.add(entry)
            await db.commit()
            await db.refresh(entry)
            
            return {
                'id': entry.id,
                'order_id': entry.order_id,
                'notes': entry.notes,
                'emotions': entry.emotions,
                'mistakes': entry.mistakes,
                'lessons': entry.lessons,
                'strategy_rating': entry.strategy_rating,
                'tags': entry.tags,
                'created_at': entry.created_at.isoformat() if entry.created_at else None
            }
    
    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific journal entry"""
        async with get_db() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(TradeJournal).where(TradeJournal.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                return None
            
            return {
                'id': entry.id,
                'order_id': entry.order_id,
                'account_id': entry.account_id,
                'notes': entry.notes,
                'emotions': entry.emotions,
                'mistakes': entry.mistakes,
                'lessons': entry.lessons,
                'strategy_rating': entry.strategy_rating,
                'tags': entry.tags,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None
            }
    
    async def get_entries_for_account(
        self,
        account_id: str,
        limit: int = 100
    ) -> list:
        """Get all journal entries for an account"""
        async with get_db() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(TradeJournal)
                .where(TradeJournal.account_id == account_id)
                .order_by(TradeJournal.created_at.desc())
                .limit(limit)
            )
            entries = result.scalars().all()
            
            return [
                {
                    'id': entry.id,
                    'order_id': entry.order_id,
                    'notes': entry.notes,
                    'emotions': entry.emotions,
                    'strategy_rating': entry.strategy_rating,
                    'tags': entry.tags,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None
                }
                for entry in entries
            ]
    
    async def update_entry(
        self,
        entry_id: str,
        notes: str = None,
        emotions: str = None,
        mistakes: str = None,
        lessons: str = None,
        strategy_rating: float = None,
        tags: str = None
    ) -> Optional[Dict[str, Any]]:
        """Update a journal entry"""
        async with get_db() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(TradeJournal).where(TradeJournal.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                return None
            
            if notes is not None:
                entry.notes = notes
            if emotions is not None:
                entry.emotions = emotions
            if mistakes is not None:
                entry.mistakes = mistakes
            if lessons is not None:
                entry.lessons = lessons
            if strategy_rating is not None:
                entry.strategy_rating = strategy_rating
            if tags is not None:
                entry.tags = tags
            
            await db.commit()
            await db.refresh(entry)
            
            return await self.get_entry(entry_id)
    
    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a journal entry"""
        async with get_db() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(TradeJournal).where(TradeJournal.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                return False
            
            await db.delete(entry)
            await db.commit()
            return True
    
    async def get_emotion_stats(self, account_id: str) -> Dict[str, Any]:
        """Get statistics about emotions in trading"""
        async with get_db() as db:
            from sqlalchemy import select, func
            
            result = await db.execute(
                select(
                    TradeJournal.emotions,
                    func.count(TradeJournal.id).label('count')
                )
                .where(TradeJournal.account_id == account_id)
                .group_by(TradeJournal.emotions)
            )
            
            emotion_counts = {row.emotions or 'unknown': row.count for row in result}
            
            # Get average strategy rating
            avg_rating_result = await db.execute(
                select(func.avg(TradeJournal.strategy_rating))
                .where(TradeJournal.account_id == account_id)
            )
            avg_rating = avg_rating_result.scalar() or 0
            
            return {
                'emotion_distribution': emotion_counts,
                'average_strategy_rating': round(avg_rating, 2),
                'total_entries': sum(emotion_counts.values())
            }


# Global instance
journal_service = JournalService()
