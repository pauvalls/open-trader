"""
Trading Journal router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.services.journal_service import journal_service

router = APIRouter()


class JournalEntryCreate(BaseModel):
    """Create a journal entry for a trade"""
    order_id: str
    notes: Optional[str] = None
    emotions: Optional[str] = Field(None, description="How you felt: calm, anxious, FOMO, confident, etc")
    mistakes: Optional[str] = None
    lessons: Optional[str] = None
    strategy_rating: Optional[float] = Field(None, ge=1, le=10, description="Rate your execution 1-10")
    tags: Optional[str] = Field(None, description="Comma-separated tags: breakout, revenge_trade, etc")


class JournalEntryUpdate(BaseModel):
    """Update a journal entry"""
    notes: Optional[str] = None
    emotions: Optional[str] = None
    mistakes: Optional[str] = None
    lessons: Optional[str] = None
    strategy_rating: Optional[float] = Field(None, ge=1, le=10)
    tags: Optional[str] = None


@router.post("/create")
async def create_journal_entry(account_id: str, entry: JournalEntryCreate):
    """Create a new journal entry for a trade"""
    try:
        result = await journal_service.create_entry(
            order_id=entry.order_id,
            account_id=account_id,
            notes=entry.notes,
            emotions=entry.emotions,
            mistakes=entry.mistakes,
            lessons=entry.lessons,
            strategy_rating=entry.strategy_rating,
            tags=entry.tags
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries/{account_id}")
async def get_journal_entries(account_id: str, limit: int = 100):
    """Get all journal entries for an account"""
    try:
        entries = await journal_service.get_entries_for_account(account_id, limit)
        return {'entries': entries, 'count': len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entry/{entry_id}")
async def get_journal_entry(entry_id: str):
    """Get a specific journal entry"""
    entry = await journal_service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.patch("/entry/{entry_id}")
async def update_journal_entry(entry_id: str, update: JournalEntryUpdate):
    """Update a journal entry"""
    result = await journal_service.update_entry(
        entry_id=entry_id,
        notes=update.notes,
        emotions=update.emotions,
        mistakes=update.mistakes,
        lessons=update.lessons,
        strategy_rating=update.strategy_rating,
        tags=update.tags
    )
    if not result:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return result


@router.delete("/entry/{entry_id}")
async def delete_journal_entry(entry_id: str):
    """Delete a journal entry"""
    success = await journal_service.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {'message': 'Journal entry deleted'}


@router.get("/stats/{account_id}")
async def get_journal_stats(account_id: str):
    """Get emotion and strategy statistics"""
    try:
        stats = await journal_service.get_emotion_stats(account_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
