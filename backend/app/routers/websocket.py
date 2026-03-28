"""
WebSocket router for real-time updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import asyncio
import json

from app.services.websocket import manager, broadcast_price_update
from app.services.market_multi import MultiMarketService

router = APIRouter()
market_service = MultiMarketService()


@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    """
    WebSocket endpoint for real-time updates
    
    Channels:
    - prices: Real-time price updates
    - agent: Agent status updates
    - trades: Trade execution updates
    - system: System status updates
    """
    await manager.connect(websocket, channel)
    
    try:
        # Send connection confirmation
        await manager.send_personal({
            'type': 'connected',
            'channel': channel,
            'message': f'Subscribed to {channel} channel'
        }, websocket)
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                action = message.get('action')
                
                if action == 'subscribe_symbol':
                    # Client wants price updates for specific symbol
                    symbol = message.get('symbol')
                    await manager.send_personal({
                        'type': 'subscribed',
                        'symbol': symbol
                    }, websocket)
                
                elif action == 'ping':
                    await manager.send_personal({'type': 'pong'}, websocket)
                
                elif action == 'get_price':
                    symbol = message.get('symbol')
                    try:
                        ticker = await market_service.get_ticker(symbol)
                        await manager.send_personal({
                            'type': 'price',
                            'symbol': symbol,
                            'data': ticker
                        }, websocket)
                    except Exception as e:
                        await manager.send_personal({
                            'type': 'error',
                            'message': str(e)
                        }, websocket)
                        
            except json.JSONDecodeError:
                await manager.send_personal({
                    'type': 'error',
                    'message': 'Invalid JSON'
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/ws")
async def websocket_default(websocket: WebSocket):
    """Default WebSocket endpoint (system channel)"""
    await websocket_endpoint(websocket, 'system')
