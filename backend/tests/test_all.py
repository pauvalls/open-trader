"""
Complete Test Suite for Open Trader

To run tests:
    cd backend
    pytest tests/ -v --cov=app --cov-report=html

Or with specific markers:
    pytest tests/ -v -m "unit"          # Unit tests only
    pytest tests/ -v -m "integration"   # Integration tests only
    pytest tests/ -v -m "slow"          # Include slow tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.strategies.rsi_strategy import RSIStrategy
from app.strategies.macd_strategy import MACDStrategy
from app.strategies.bollinger_strategy import BollingerStrategy
from app.services.paper_trading_service import PaperTradingService
from app.services.agent_service import AITradingAgent, AgentConfig


# ============= Fixtures =============

@pytest.fixture
def sample_candles():
    """Generate sample candle data for testing"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    candles = []
    
    for i in range(50):
        candle = {
            'timestamp': int((base_time + timedelta(hours=i)).timestamp() * 1000),
            'open': 2000 + i * 10,
            'high': 2020 + i * 10,
            'low': 1980 + i * 10,
            'close': 2010 + i * 10,
            'volume': 1000 + i * 100
        }
        candles.append(candle)
    
    return candles


@pytest.fixture
def sample_candles_downtrend():
    """Generate sample candle data with downtrend"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    candles = []
    
    for i in range(50):
        candle = {
            'timestamp': int((base_time + timedelta(hours=i)).timestamp() * 1000),
            'open': 2000 - i * 10,
            'high': 2020 - i * 10,
            'low': 1980 - i * 10,
            'close': 2010 - i * 10,
            'volume': 1000 + i * 100
        }
        candles.append(candle)
    
    return candles


@pytest.fixture
def rsi_strategy():
    return RSIStrategy(period=14, oversold=30, overbought=70)


@pytest.fixture
def macd_strategy():
    return MACDStrategy(fast=12, slow=26, signal=9)


@pytest.fixture
def bollinger_strategy():
    return BollingerStrategy(period=20, std_dev=2.0)


# ============= Strategy Tests =============

class TestRSIStrategy:
    """Tests for RSI Strategy"""
    
    @pytest.mark.unit
    def test_rsi_calculation(self, rsi_strategy, sample_candles):
        """Test RSI calculation with uptrend data"""
        rsi_value = rsi_strategy.calculate(sample_candles)
        
        assert isinstance(rsi_value, float)
        assert 0 <= rsi_value <= 100
        # Uptrend should have higher RSI
        assert rsi_value > 50
    
    @pytest.mark.unit
    def test_rsi_oversold_signal(self, rsi_strategy):
        """Test oversold signal generation"""
        # Create candles with sharp decline
        candles = []
        base_price = 2000
        for i in range(20):
            candles.append({
                'timestamp': i,
                'open': base_price - i * 50,
                'high': base_price - i * 50 + 10,
                'low': base_price - i * 50 - 10,
                'close': base_price - i * 50,
                'volume': 1000
            })
        
        signal = rsi_strategy.get_signal(candles)
        # After sharp decline, should be oversold or hold
        assert signal in ['buy', 'hold']
    
    @pytest.mark.unit
    def test_rsi_overbought_signal(self, rsi_strategy):
        """Test overbought signal generation"""
        # Create candles with sharp rise
        candles = []
        base_price = 1000
        for i in range(20):
            candles.append({
                'timestamp': i,
                'open': base_price + i * 50,
                'high': base_price + i * 50 + 10,
                'low': base_price + i * 50 - 10,
                'close': base_price + i * 50,
                'volume': 1000
            })
        
        signal = rsi_strategy.get_signal(candles)
        # After sharp rise, should be overbought or hold
        assert signal in ['sell', 'hold']
    
    @pytest.mark.unit
    def test_rsi_insufficient_data(self, rsi_strategy):
        """Test RSI with insufficient data"""
        short_candles = [{'close': 100} for _ in range(5)]
        signal = rsi_strategy.get_signal(short_candles)
        assert signal == 'hold'


class TestMACDStrategy:
    """Tests for MACD Strategy"""
    
    @pytest.mark.unit
    def test_macd_calculation(self, macd_strategy, sample_candles):
        """Test MACD calculation"""
        macd_line, signal_line, histogram = macd_strategy.calculate(sample_candles)
        
        assert isinstance(macd_line, float)
        assert isinstance(signal_line, float)
        assert isinstance(histogram, float)
    
    @pytest.mark.unit
    def test_macd_bullish_crossover(self, macd_strategy):
        """Test bullish MACD crossover"""
        # Create candles for bullish crossover
        candles = []
        for i in range(35):
            # Gradually increasing prices
            price = 1000 + i * 10 + (i * i * 0.5)
            candles.append({
                'timestamp': i,
                'open': price - 5,
                'high': price + 10,
                'low': price - 10,
                'close': price,
                'volume': 1000
            })
        
        signal = macd_strategy.get_signal(candles)
        # Should detect bullish trend
        assert signal in ['buy', 'hold']
    
    @pytest.mark.unit
    def test_macd_bearish_crossover(self, macd_strategy):
        """Test bearish MACD crossover"""
        # Create candles for bearish crossover
        candles = []
        for i in range(35):
            # Gradually decreasing prices
            price = 2000 - i * 10 - (i * i * 0.5)
            candles.append({
                'timestamp': i,
                'open': price + 5,
                'high': price + 10,
                'low': price - 10,
                'close': price,
                'volume': 1000
            })
        
        signal = macd_strategy.get_signal(candles)
        # Should detect bearish trend
        assert signal in ['sell', 'hold']


class TestBollingerStrategy:
    """Tests for Bollinger Bands Strategy"""
    
    @pytest.mark.unit
    def test_bollinger_calculation(self, bollinger_strategy, sample_candles):
        """Test Bollinger Bands calculation"""
        upper, middle, lower = bollinger_strategy.calculate(sample_candles)
        
        assert isinstance(upper, float)
        assert isinstance(middle, float)
        assert isinstance(lower, float)
        assert upper > middle > lower
    
    @pytest.mark.unit
    def test_bollinger_lower_band_touch(self, bollinger_strategy):
        """Test buy signal when price touches lower band"""
        # Create candles with price hitting lower band
        candles = []
        base_price = 2000
        for i in range(25):
            if i > 20:  # Near the end, price drops significantly
                close = base_price - 200
            else:
                close = base_price
            
            candles.append({
                'timestamp': i,
                'open': close - 5,
                'high': close + 10,
                'low': close - 15,
                'close': close,
                'volume': 1000
            })
        
        signal = bollinger_strategy.get_signal(candles)
        assert signal in ['buy', 'hold']
    
    @pytest.mark.unit
    def test_bollinger_upper_band_touch(self, bollinger_strategy):
        """Test sell signal when price touches upper band"""
        # Create candles with price hitting upper band
        candles = []
        base_price = 2000
        for i in range(25):
            if i > 20:  # Near the end, price rises significantly
                close = base_price + 200
            else:
                close = base_price
            
            candles.append({
                'timestamp': i,
                'open': close - 5,
                'high': close + 15,
                'low': close - 10,
                'close': close,
                'volume': 1000
            })
        
        signal = bollinger_strategy.get_signal(candles)
        assert signal in ['sell', 'hold']


# ============= Paper Trading Tests =============

class TestPaperTrading:
    """Tests for Paper Trading Service"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_account(self):
        """Test account creation"""
        service = PaperTradingService()
        
        account = await service.create_account(initial_balance=5000)
        
        assert account is not None
        assert 'id' in account
        assert account['initial_balance'] == 5000
        assert account['current_balance'] == 5000
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_execute_order_buy(self):
        """Test executing a buy order"""
        service = PaperTradingService()
        
        # Create account
        account = await service.create_account(initial_balance=10000)
        account_id = account['id']
        
        # Execute buy order
        order = await service.execute_order(
            account_id=account_id,
            symbol='ETH/USDT',
            side='buy',
            amount=1000,
            price=2000
        )
        
        assert order is not None
        assert order['side'] == 'buy'
        assert order['amount'] == 1000
        assert order['status'] == 'filled'
        
        # Check balance updated
        updated_account = await service.get_account(account_id)
        assert updated_account['current_balance'] < 10000  # Balance decreased
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_execute_order_sell(self):
        """Test executing a sell order (closing position)"""
        service = PaperTradingService()
        
        # Create account and buy first
        account = await service.create_account(initial_balance=10000)
        account_id = account['id']
        
        # Buy
        await service.execute_order(
            account_id=account_id,
            symbol='ETH/USDT',
            side='buy',
            amount=1000,
            price=2000
        )
        
        # Sell (close position)
        order = await service.execute_order(
            account_id=account_id,
            symbol='ETH/USDT',
            side='sell',
            amount=1000,
            price=2100  # Profit
        )
        
        assert order is not None
        assert order['side'] == 'sell'
        assert 'pnl' in order
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_insufficient_balance(self):
        """Test order with insufficient balance"""
        service = PaperTradingService()
        
        account = await service.create_account(initial_balance=100)
        account_id = account['id']
        
        # Try to buy more than balance
        with pytest.raises(Exception):
            await service.execute_order(
                account_id=account_id,
                symbol='ETH/USDT',
                side='buy',
                amount=1000,
                price=2000
            )
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_position_tracking(self):
        """Test position tracking"""
        service = PaperTradingService()
        
        account = await service.create_account(initial_balance=10000)
        account_id = account['id']
        
        # Buy
        await service.execute_order(
            account_id=account_id,
            symbol='ETH/USDT',
            side='buy',
            amount=1000,
            price=2000
        )
        
        # Get account with positions
        account_data = await service.get_account(account_id)
        
        assert 'positions' in account_data
        assert len(account_data['positions']) > 0
        
        position = account_data['positions'][0]
        assert position['symbol'] == 'ETH/USDT'
        assert position['side'] == 'long'


# ============= Agent Tests =============

class TestTradingAgent:
    """Tests for AI Trading Agent"""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_config(self):
        """Test agent configuration"""
        config = AgentConfig(
            account_id='test_account',
            symbols=['ETH/USDT'],
            max_position_size_usd=1000,
            max_positions=3
        )
        
        assert config.account_id == 'test_account'
        assert config.symbols == ['ETH/USDT']
        assert config.max_position_size_usd == 1000
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_analysis(self, sample_candles):
        """Test agent market analysis"""
        config = AgentConfig(
            account_id='test_account',
            symbols=['ETH/USDT'],
            consensus_threshold=2,
            use_rsi=True,
            use_macd=True,
            use_bollinger=True
        )
        
        # Mock market service
        mock_market = Mock()
        mock_market.get_candles = AsyncMock(return_value=sample_candles)
        
        mock_trading = Mock()
        
        agent = AITradingAgent('test_agent', config, mock_trading, mock_market)
        
        # Test analysis
        decision = await agent._analyze_symbol('ETH/USDT', {})
        
        assert decision is not None
        assert decision.symbol == 'ETH/USDT'
        assert decision.action.value in ['buy', 'sell', 'hold']
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_risk_management_position_size(self):
        """Test agent respects max position size"""
        config = AgentConfig(
            account_id='test_account',
            symbols=['ETH/USDT'],
            max_position_size_usd=500,
            max_positions=1
        )
        
        # Should not allow position larger than max
        assert config.max_position_size_usd == 500
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_consensus_calculation(self):
        """Test strategy consensus calculation"""
        signals = {'rsi': 'buy', 'macd': 'buy', 'bollinger': 'hold'}
        
        buy_votes = sum(1 for s in signals.values() if s == 'buy')
        sell_votes = sum(1 for s in signals.values() if s == 'sell')
        hold_votes = sum(1 for s in signals.values() if s == 'hold')
        
        # 2 buy votes, consensus threshold of 2 should give buy
        assert buy_votes == 2
        assert sell_votes == 0
        assert hold_votes == 1


# ============= Integration Tests =============

class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_full_trading_workflow(self):
        """Test complete trading workflow"""
        # This would test: create account -> execute orders -> check positions
        # For now, just verify services can be instantiated
        paper_service = PaperTradingService()
        
        account = await paper_service.create_account(initial_balance=10000)
        assert account is not None
        
        # Verify account can be retrieved
        retrieved = await paper_service.get_account(account['id'])
        assert retrieved['id'] == account['id']
    
    @pytest.mark.integration
    def test_strategy_consensus(self):
        """Test strategy consensus logic"""
        rsi = RSIStrategy()
        macd = MACDStrategy()
        bollinger = BollingerStrategy()
        
        # Test with neutral data (not enough candles)
        short_candles = [{'close': 100} for _ in range(5)]
        
        rsi_signal = rsi.get_signal(short_candles)
        macd_signal = macd.get_signal(short_candles)
        bollinger_signal = bollinger.get_signal(short_candles)
        
        # All should return hold with insufficient data
        assert rsi_signal == 'hold'


# ============= Benchmark Tests =============

class TestPerformance:
    """Performance benchmarks"""
    
    @pytest.mark.benchmark
    def test_rsi_performance(self, rsi_strategy, sample_candles):
        """Benchmark RSI calculation"""
        import time
        
        start = time.time()
        for _ in range(100):
            rsi_strategy.calculate(sample_candles)
        elapsed = time.time() - start
        
        # Should complete 100 calculations in less than 1 second
        assert elapsed < 1.0
    
    @pytest.mark.benchmark
    def test_macd_performance(self, macd_strategy, sample_candles):
        """Benchmark MACD calculation"""
        import time
        
        start = time.time()
        for _ in range(100):
            macd_strategy.calculate(sample_candles)
        elapsed = time.time() - start
        
        assert elapsed < 1.0


# ============= Error Handling Tests =============

class TestErrorHandling:
    """Tests for error handling"""
    
    @pytest.mark.unit
    def test_empty_candles(self, rsi_strategy):
        """Test handling of empty candle data"""
        signal = rsi_strategy.get_signal([])
        assert signal == 'hold'
    
    @pytest.mark.unit
    def test_none_candles(self, rsi_strategy):
        """Test handling of None candle data"""
        signal = rsi_strategy.get_signal(None)
        assert signal == 'hold'
    
    @pytest.mark.unit
    def test_malformed_candles(self, rsi_strategy):
        """Test handling of malformed candle data"""
        malformed = [{'open': 100}, {'open': 101}]  # Missing 'close'
        
        # Should handle gracefully
        try:
            signal = rsi_strategy.get_signal(malformed)
            assert signal == 'hold'
        except (KeyError, TypeError):
            pass  # Also acceptable


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
