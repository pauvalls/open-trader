"""
Export router for trading data
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Optional

from app.services.export_service import export_service

router = APIRouter()


@router.get("/trades/csv/{account_id}", response_class=PlainTextResponse)
async def export_trades_csv(account_id: str):
    """
    Export all trades for an account as CSV
    
    Can be opened in Excel, Google Sheets, etc.
    """
    try:
        csv_data = await export_service.export_trades_csv(account_id)
        return PlainTextResponse(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=trades_{account_id}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/json/{account_id}")
async def export_trades_json(account_id: str):
    """Export all trades for an account as JSON"""
    try:
        data = await export_service.export_trades_json(account_id)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{account_id}")
async def export_full_report(account_id: str):
    """
    Export full trading report with analytics
    
    Includes:
    - Account summary
    - Trade statistics (win rate, profit factor, etc.)
    - All trades
    - Open positions
    """
    try:
        report = await export_service.export_full_report(account_id)
        if 'error' in report:
            raise HTTPException(status_code=404, detail=report['error'])
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/json/{account_id}")
async def export_positions_json(account_id: str):
    """Export all positions for an account as JSON"""
    try:
        data = await export_service.export_positions_json(account_id)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
