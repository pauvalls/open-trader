# Open Trader Test Suite

Complete test suite for the Open Trader algorithmic trading platform.

## Quick Start

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=html

# Run specific test categories
pytest tests/ -v -m "unit"         # Unit tests only
pytest tests/ -v -m "integration"  # Integration tests
pytest tests/ -v -m "not slow"     # Exclude slow tests
```

## Test Structure

```
tests/
├── __init__.py
├── test_all.py          # Main test suite (strategies, paper trading, agent)
├── test_user_config.py  # User configuration and encryption tests
├── test_market.py       # Market data and integration tests
└── conftest.py          # Shared fixtures (optional)
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
Fast tests that don't require external services:
- RSI/MACD/Bollinger calculations
- Signal generation
- Position tracking
- Encryption/decryption

### Integration Tests (`@pytest.mark.integration`)
Tests that use database or external APIs:
- Account creation
- Order execution
- Real market data fetching
- Database persistence

### Slow Tests (`@pytest.mark.slow`)
Long-running tests:
- Performance benchmarks
- Extended trading simulations
- Multi-provider fallback tests

### Benchmark Tests (`@pytest.mark.benchmark`)
Performance measurements:
- Strategy calculation speed
- Database query performance
- API response times

## Test Coverage Areas

### Strategies (test_all.py::TestRSIStrategy, TestMACDStrategy, TestBollingerStrategy)
- [x] RSI calculation with various data
- [x] MACD line/signal/histogram
- [x] Bollinger Bands upper/middle/lower
- [x] Buy/sell/hold signal generation
- [x] Edge cases (insufficient data, empty candles)

### Paper Trading (test_all.py::TestPaperTrading)
- [x] Account creation
- [x] Order execution (buy/sell)
- [x] Balance updates
- [x] Position tracking
- [x] P&L calculation
- [x] Insufficient balance handling

### AI Agent (test_all.py::TestTradingAgent)
- [x] Agent configuration
- [x] Strategy consensus
- [x] Risk management
- [x] Position sizing

### User Configuration (test_user_config.py)
- [x] API key encryption/decryption
- [x] Config validation
- [x] Security (key not in responses)

### Market Data (test_market.py)
- [x] Symbol normalization
- [x] Candle data structure
- [x] OHLC validation
- [x] Real API integration

## Writing New Tests

```python
import pytest

@pytest.mark.unit
def test_new_feature():
    """Description of what this test verifies"""
    # Arrange
    input_data = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value

@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_feature():
    """Test async functionality"""
    result = await async_function()
    assert result is not None
```

## Continuous Integration

To run tests in CI/CD:

```yaml
# .github/workflows/test.yml example
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest backend/tests/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## Known Issues

1. **Market data tests require internet** - May fail in air-gapped environments
2. **Database tests need SQLite/PostgreSQL** - Configure DATABASE_URL for PostgreSQL tests
3. **Rate limiting** - Real API tests may hit rate limits during heavy testing

## Tips

- Use `@pytest.mark.skip(reason="...")` to temporarily skip failing tests
- Use `@pytest.mark.xfail(reason="...")` for known bugs
- Use `pytest -k "test_name"` to run specific tests
- Use `pytest --pdb` to drop into debugger on failure
