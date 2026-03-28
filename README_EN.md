# Open Trader

Algorithmic cryptocurrency trading system with paper trading support and real execution on Uniswap V3.

## ✨ Features

- **📊 Paper Trading**: Simulate trades with fake money using real market prices
- **📈 Strategies**: RSI, MACD, Bollinger Bands + multi-strategy consensus system
- **🔔 Alerts**: Real-time notifications via Telegram and Discord
- **📱 Dashboard**: Real-time web interface to monitor operations
- **🔗 Uniswap V3**: Ready for live trading on Arbitrum/Base
- **🏠 Self-hosted**: You control your keys and your instance

## 📁 Structure

```
open-trader/
├── backend/           # FastAPI + trading logic
│   ├── app/
│   │   ├── routers/   # API endpoints (paper, market, strategies, dashboard)
│   │   ├── services/  # Market data, alerts
│   │   └── strategies/# RSI, MACD, Bollinger implementations
│   ├── main.py
│   └── requirements.txt
├── Dockerfile         # Production-optimized multi-stage build
├── railway.toml       # Railway deployment configuration
├── docker-compose.yml # Easy self-hosting
└── README.md
```

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Clone and enter
git clone https://github.com/pauvalls/open-trader.git
cd open-trader

# Configure
cp backend/.env.example backend/.env
# Edit backend/.env with your variables (see Configuration)

# Start
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Local Python

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Railway (One-Click Deploy)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-url)

See [RAILWAY.md](RAILWAY.md) for detailed instructions.

## 🌐 Access

Once running:

- **Dashboard**: http://localhost:8000/dashboard/
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/

## ⚙️ Configuration

Edit `backend/.env`:

```env
# API
DEBUG=true
SECRET_KEY=your-very-long-secret-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/paper_trading.db

# Alerts (optional but recommended)
TELEGRAM_BOT_TOKEN=your-botfather-token
TELEGRAM_CHAT_ID=your-chat-id
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Getting Alert Credentials:

**Telegram:**
1. Talk to [@BotFather](https://t.me/botfather)
2. Create new bot (`/newbot`)
3. Copy the token
4. Send a message to your bot
5. Visit `https://api.telegram.org/bot[YOUR_TOKEN]/getUpdates` to see your chat_id

**Discord:**
1. In your server: Server Settings → Integrations → Webhooks
2. New Webhook → Copy URL

## 📊 Available Strategies

| Strategy | Description | Parameters |
|----------|-------------|------------|
| **RSI** | Buy RSI<30, Sell RSI>70 | period, oversold, overbought |
| **MACD** | MACD and signal line crossover | fast, slow, signal |
| **Bollinger** | Bollinger Bands trading | period, std_dev, use_confirmation |

### Multi-Strategy Consensus

The `/strategies/scan` endpoint combines all 3 strategies and generates a consensus signal:
- **BUY**: 2+ strategies indicate buy
- **SELL**: 2+ strategies indicate sell
- **HOLD**: No clear consensus

## 🔌 Main API Endpoints

### Paper Trading
```bash
# Create account
POST /paper/account
{"initial_balance": 10000}

# View account
GET /paper/account/{id}

# Execute order
POST /paper/order
{
  "account_id": "uuid",
  "symbol": "ETH/USDT",
  "side": "buy",
  "amount": 0.5
}

# History
GET /paper/orders/{account_id}
```

### Strategies
```bash
# List
GET /strategies

# Current signal
GET /strategies/rsi/signal?symbol=ETH/USDT&timeframe=1h

# Backtest
POST /strategies/rsi/backtest
{
  "symbol": "ETH/USDT",
  "timeframe": "1h",
  "initial_balance": 10000,
  "strategy_params": {"rsi_period": 14}
}

# Multi-strategy scan
GET /strategies/scan?symbol=BTC/USDT
```

### Market Data
```bash
# Current price
GET /market/price/ETH/USDT

# Historical candles
GET /market/klines/ETH/USDT?timeframe=1h&limit=100

# Available pairs
GET /market/tickers
```

## 📱 Dashboard

Access `/dashboard/` to see:
- Balance and P&L in real-time
- Open positions
- Active signals (auto-refresh every 5s)
- Order history
- Real-time logs

## 🔔 Alerts

Alerts are sent automatically when:
- A trading signal is detected (buy/sell)
- An order is executed
- There's multi-strategy consensus

Configure TELEGRAM_BOT_TOKEN and DISCORD_WEBHOOK_URL in `.env` to receive them.

## 🗺️ Roadmap

### Phase 1: Paper Trading ✅
- [x] Paper trading system
- [x] Multiple strategies (RSI, MACD, Bollinger)
- [x] Telegram/Discord alerts
- [x] Real-time dashboard
- [ ] Machine learning for strategies

### Phase 2: Live Trading 🔄
- [ ] Uniswap V3 integration
- [ ] Gas and slippage management
- [ ] Security protections (stop-loss, limits)
- [ ] On-chain analysis

### Phase 3: Advanced
- [ ] Portfolio rebalancing
- [ ] Arbitrage detection
- [ ] Yield farming automation

## ⚠️ Disclaimer

This software is for educational purposes. Cryptocurrency trading involves significant risks:
- Never invest more than you can afford to lose
- Test extensively in paper trading before using real money
- Review each operation before confirming
- I (Kimi Claw) am not a financial advisor

## 🤝 Contributing

This is an actively developed project. Suggestions and PRs are welcome.

## 📄 License

MIT - Use at your own risk.

---

## 🌍 Translations

- [Español](README.md)
- [English](README_EN.md)
