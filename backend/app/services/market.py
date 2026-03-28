"""Market data service using Binance"""

import asyncio
from typing import Optional, List, Dict
from datetime import datetime
import ccxt.async_support as ccxt


class MarketService:
    """Servicio para obtener datos de mercado de Binance"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
        self.last_update = None
        self._cache = {}
        self._cache_ttl = 5  # segundos
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Obtener precio actual de un par"""
        try:
            # Normalizar símbolo (ETH/USDC -> ETH/USDC)
            ticker = await self.exchange.fetch_ticker(symbol)
            self.last_update = datetime.utcnow()
            return ticker.get('last')
        except Exception as e:
            print(f"Error obteniendo precio para {symbol}: {e}")
            return None
    
    async def get_klines(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 100
    ) -> Optional[List[Dict]]:
        """
        Obtener velas históricas (OHLCV)
        
        Returns: Lista de diccionarios con:
            - timestamp
            - open
            - high
            - low
            - close
            - volume
        """
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            data = []
            for candle in ohlcv:
                data.append({
                    'timestamp': candle[0],
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            return data
        except Exception as e:
            print(f"Error obteniendo klines para {symbol}: {e}")
            return None
    
    async def get_available_tickers(self) -> List[str]:
        """Obtener lista de pares disponibles"""
        try:
            markets = await self.exchange.load_markets()
            # Filtrar solo pares USDT para trading sencillo
            usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
            return sorted(usdt_pairs)[:100]  # Limitar a 100 principales
        except Exception as e:
            print(f"Error cargando mercados: {e}")
            return []
    
    async def close(self):
        """Cerrar conexión"""
        await self.exchange.close()
