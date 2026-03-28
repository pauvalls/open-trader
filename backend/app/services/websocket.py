"""
WebSocket Manager for real-time updates
"""

import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            'prices': [],
            'agent': [],
            'trades': [],
            'system': []
        }
    
    async def connect(self, websocket: WebSocket, channel: str = 'system'):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str = 'system'):
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
    
    async def broadcast(self, message: dict, channel: str = 'system'):
        """Broadcast to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections[channel]:
                self.active_connections[channel].remove(conn)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send to specific client"""
        try:
            await websocket.send_json(message)
        except:
            pass


# Global manager instance
manager = ConnectionManager()


async def broadcast_price_update(symbol: str, price: float, change_24h: float = None):
    """Broadcast price update to all price subscribers"""
    await manager.broadcast({
        'type': 'price_update',
        'symbol': symbol,
        'price': price,
        'change_24h': change_24h,
        'timestamp': asyncio.get_event_loop().time()
    }, channel='prices')


async def broadcast_agent_update(agent_id: str, status: str, data: dict = None):
    """Broadcast agent status update"""
    await manager.broadcast({
        'type': 'agent_update',
        'agent_id': agent_id,
        'status': status,
        'data': data or {},
        'timestamp': asyncio.get_event_loop().time()
    }, channel='agent')


async def broadcast_trade_update(account_id: str, trade: dict):
    """Broadcast new trade to subscribers"""
    await manager.broadcast({
        'type': 'trade_update',
        'account_id': account_id,
        'trade': trade,
        'timestamp': asyncio.get_event_loop().time()
    }, channel='trades')


async def broadcast_system_status(status: str, message: str = None):
    """Broadcast system status"""
    await manager.broadcast({
        'type': 'system_status',
        'status': status,
        'message': message,
        'timestamp': asyncio.get_event_loop().time()
    }, channel='system')
