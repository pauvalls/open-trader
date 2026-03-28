"""
Strategy Base Class with async get_signal support
"""

from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    @abstractmethod
    def get_signal(self, df: pd.DataFrame) -> Dict:
        """Get trading signal from DataFrame"""
        pass
    
    async def get_signal_async(self, symbol: str, timeframe: str, market_service) -> str:
        """
        Async method to fetch data and return signal
        
        Returns: 'buy', 'sell', or 'hold'
        """
        try:
            # Get candles from market service
            candles = await market_service.get_candles(symbol, timeframe, limit=100)
            
            if not candles or len(candles) < 30:
                return 'hold'
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Get signal
            result = self.get_signal(df)
            return result.get('action', 'hold')
            
        except Exception as e:
            print(f"Error getting signal for {symbol}: {e}")
            return 'hold'
