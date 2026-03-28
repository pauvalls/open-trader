#!/bin/bash
# Quick test script for Open Trader

echo "🧪 Testing Open Trader Backend..."

cd "$(dirname "$0")"

# Check Python version
echo "✓ Python version: $(python3 --version)"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run basic import test
echo "🔍 Testing imports..."
python3 -c "
from fastapi import FastAPI
from app.database import Base
from app.services.market import MarketService
from app.strategies.rsi_strategy import RSIStrategy
print('✓ All imports successful')
"

# Test RSI calculation
echo "📊 Testing RSI strategy..."
python3 -c "
import pandas as pd
from app.strategies.rsi_strategy import RSIStrategy

# Create sample data
data = pd.DataFrame({
    'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109] * 3
})

strategy = RSIStrategy()
signal = strategy.get_signal(data)
print(f'✓ RSI signal: {signal}')
"

echo ""
echo "✅ All tests passed!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  cd backend"
echo "  uvicorn main:app --reload --host 0.0.0.0 --port 8000"
