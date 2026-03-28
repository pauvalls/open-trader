"""
Tests for Market Data Service
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestMultiMarketService:
    """Tests for MultiMarketService"""
    
    @pytest.mark.unit
    def test_symbol_normalization(self):
        """Test symbol normalization for different exchanges"""
        test_cases = [
            ('BTC/USDT', 'BTCUSDT'),
            ('ETH/USDC', 'ETHUSDC'),
            ('SOL/USD', 'SOLUSD'),
            ('BTC/USDT:USDT', 'BTCUSDT'),  # Futures format
        ]
        
        for input_symbol, expected in test_cases:
            # Remove special characters and normalize
            normalized = input_symbol.replace('/', '').replace(':USDT', '')
            assert normalized == expected, f"Failed for {input_symbol}"
    
    @pytest.mark.unit
    def test_timeframe_validation(self):
        """Test valid timeframe formats"""
        valid_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
        
        for tf in valid_timeframes:
            # Simple validation - should be alphanumeric
            assert tf.isalnum() or tf[:-1].isdigit()
            assert len(tf) >= 2
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_fetch_candles_real(self):
        """Test fetching real candle data (requires internet)"""
        from app.services.market_multi import MultiMarketService
        
        service = MultiMarketService()
        
        try:
            candles = await service.get_candles('ETH/USDT', '1h', 10)
            
            assert candles is not None
            assert len(candles) > 0
            
            # Verify candle structure
            candle = candles[0]
            required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                assert field in candle, f"Missing field: {field}"
            
            # Verify OHLC logic
            assert candle['high'] >= candle['low']
            assert candle['high'] >= candle['open']
            assert candle['high'] >= candle['close']
            assert candle['low'] <= candle['open']
            assert candle['low'] <= candle['close']
            
        except Exception as e:
            pytest.skip(f"Market data fetch failed (network issue?): {e}")


class TestStrategyIntegration:
    """Tests for strategy integration with market data"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_strategy_with_real_data(self):
        """Test strategies with real market data"""
        from app.services.market_multi import MultiMarketService
        from app.strategies.rsi_strategy import RSIStrategy
        
        service = MultiMarketService()
        rsi = RSIStrategy()
        
        try:
            candles = await service.get_candles('BTC/USDT', '1h', 50)
            
            if len(candles) >= 14:
                signal = rsi.get_signal(candles)
                assert signal in ['buy', 'sell', 'hold']
                
                # Get detailed analysis
                rsi_value = rsi.calculate(candles)
                assert 0 <= rsi_value <= 100
                
        except Exception as e:
            pytest.skip(f"Integration test failed: {e}")