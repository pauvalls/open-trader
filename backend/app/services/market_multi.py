"""Multi-provider market data service with automatic failover"""

import asyncio
from typing import Optional, List, Dict
from datetime import datetime
import ccxt.async_support as ccxt


class MultiMarketService:
    """
    Servicio de datos de mercado con múltiples proveedores.
    
    Si un exchange falla, automáticamente prueba el siguiente.
    Orden de preferencia: Binance → Bybit → Kraken → KuCoin
    """
    
    PROVIDERS = [
        ('binance', ccxt.binance),
        ('bybit', ccxt.bybit),
        ('kraken', ccxt.kraken),
        ('kucoin', ccxt.kucoin),
    ]
    
    def __init__(self):
        self.last_update = None
        self._cache = {}
        self._cache_ttl = 5
        self._current_provider = None
    
    async def _try_provider(self, provider_name, provider_class, method, *args, **kwargs):
        """Intentar obtener datos de un provider específico"""
        exchange = None
        try:
            exchange = provider_class({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            result = await method(exchange, *args, **kwargs)
            self._current_provider = provider_name
            await exchange.close()
            return result
        except Exception as e:
            if exchange:
                try:
                    await exchange.close()
                except:
                    pass
            raise e
    
    async def _fetch_with_fallback(self, method, *args, **kwargs):
        """Obtener datos con fallback automático entre providers"""
        errors = []
        
        for name, provider_class in self.PROVIDERS:
            try:
                result = await self._try_provider(name, provider_class, method, *args, **kwargs)
                self.last_update = datetime.utcnow()
                return result
            except Exception as e:
                errors.append(f"{name}: {str(e)[:50]}")
                continue
        
        # Todos los providers fallaron
        print(f"All providers failed: {' | '.join(errors)}")
        return None
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Obtener precio actual con fallback"""
        async def _fetch(exchange, sym):
            ticker = await exchange.fetch_ticker(sym)
            return ticker.get('last')
        
        return await self._fetch_with_fallback(_fetch, symbol)
    
    async def get_klines(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 100
    ) -> Optional[List[Dict]]:
        """
        Obtener velas históricas con fallback entre exchanges
        
        Returns: Lista de diccionarios con OHLCV
        """
        async def _fetch(exchange, sym, tf, lim):
            ohlcv = await exchange.fetch_ohlcv(sym, tf, limit=lim)
            
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
        
        return await self._fetch_with_fallback(_fetch, symbol, timeframe, limit)
    
    async def get_available_tickers(self) -> List[str]:
        """Obtener lista de pares disponibles (desde Binance principalmente)"""
        try:
            exchange = ccxt.binance({'enableRateLimit': True})
            markets = await exchange.load_markets()
            await exchange.close()
            
            usdt_pairs = [s for s in markets.keys() if s.endswith('/USDT')]
            return sorted(usdt_pairs)[:100]
        except Exception as e:
            print(f"Error cargando mercados: {e}")
            # Fallback básico
            return [
                'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT',
                'ARB/USDT', 'OP/USDT', 'LINK/USDT', 'UNI/USDT',
                'AAVE/USDT', 'MKR/USDT', 'LDO/USDT', 'CRV/USDT'
            ]
    
    def get_current_provider(self) -> Optional[str]:
        """Devuelve qué provider se usó en la última llamada"""
        return self._current_provider


# Singleton para reusar en toda la app
_market_service = None

def get_market_service() -> MultiMarketService:
    """Obtener instancia singleton del servicio"""
    global _market_service
    if _market_service is None:
        _market_service = MultiMarketService()
    return _market_service
