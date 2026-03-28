<div align="center">

# 🤖 Open Trader

**Algorithmic Crypto Trading System with AI Agent**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/open-trader)

[English](#english) | [Español](#español)

</div>

---

<a name="english"></a>
## 🇬🇧 English

### ✨ Features

| Feature | Description |
|---------|-------------|
| **🤖 AI Trading Agent** | Autonomous trading bot with technical strategies + optional AI analysis |
| **📊 Paper Trading** | Practice with fake money using real market prices |
| **🧠 Multi-Strategy** | RSI, MACD, Bollinger Bands with consensus system |
| **🎯 Advanced Orders** | Limit, Stop-Loss, Trailing Stop, Bracket Orders |
| **🏦 Multi-DEX** | Uniswap V3, PancakeSwap V3, SushiSwap V3 support |
| **🔔 Alerts** | Telegram & Discord notifications |
| **📱 Dashboard** | Real-time web UI with charts |
| **🌍 i18n** | English & Spanish support |

### 🚀 Quick Deploy

#### Railway (One Click)

1. Click the button above
2. Add your environment variables (optional):
   - `KIMI_API_KEY` - For AI-enhanced trading
   - `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` - For alerts
3. Done! Your dashboard will be live in ~2 minutes

#### Docker

```bash
git clone https://github.com/pauvalls/open-trader.git
cd open-trader
cp backend/.env.example backend/.env
# Edit backend/.env with your settings
docker-compose up -d
```

### 🎮 AI Agent Usage

**Create an Agent:**
```bash
curl -X POST https://your-app.railway.app/agent/create/my-agent \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "your-account-id",
    "symbols": ["ETH/USDT", "BTC/USDT"],
    "preset": "balanced",
    "kimi_api_key": "optional-kimi-key-for-ai-mode"
  }'
```

**Control:**
```bash
# Start
curl -X POST https://your-app.railway.app/agent/control/my-agent \
  -d '{"action": "start"}'

# Check status
curl https://your-app.railway.app/agent/status/my-agent
```

### 🧠 How the AI Agent Works

**Mode 1: Technical Strategies (Default)**
- Monitors market every 15 minutes
- Uses RSI + MACD + Bollinger Bands
- Executes when 2/3 strategies agree (configurable)
- No AI involved - pure technical analysis

**Mode 2: AI-Enhanced (Optional)**
- Same technical analysis
- PLUS: Sends market data to Kimi AI for additional validation
- Only trades when both AI + strategies agree
- Requires `KIMI_API_KEY`

### 📁 Structure

```
open-trader/
├── backend/           # FastAPI + trading logic
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Market, alerts, AI agent
│   │   └── strategies/# RSI, MACD, Bollinger
│   ├── main.py
│   └── requirements.txt
├── Dockerfile
├── railway.json       # Railway template config
└── docker-compose.yml
```

### 🔧 Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL URL (auto-set by Railway) | Auto |
| `KIMI_API_KEY` | Moonshot AI API key | Optional |
| `TELEGRAM_BOT_TOKEN` | Telegram bot for alerts | Optional |
| `DISCORD_WEBHOOK_URL` | Discord webhook | Optional |

---

<a name="español"></a>
## 🇪🇸 Español

### ✨ Características

| Característica | Descripción |
|----------------|-------------|
| **🤖 Agente AI** | Bot de trading autónomo con estrategias + IA opcional |
| **📊 Paper Trading** | Practica con dinero ficticio y precios reales |
| **🧠 Multi-Estrategia** | RSI, MACD, Bollinger con sistema de consenso |
| **🎯 Órdenes Avanzadas** | Limit, Stop-Loss, Trailing Stop, Bracket Orders |
| **🏦 Multi-DEX** | Soporte Uniswap V3, PancakeSwap V3, SushiSwap V3 |
| **🔔 Alertas** | Notificaciones Telegram y Discord |
| **📱 Dashboard** | Interfaz web en tiempo real |
| **🌍 i18n** | Soporte Español e Inglés |

### 🚀 Deploy Rápido

#### Railway (Un Click)

1. Haz click en el botón de arriba
2. Añade variables de entorno (opcional):
   - `KIMI_API_KEY` - Para modo IA mejorado
   - `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` - Para alertas
3. ¡Listo! Tu dashboard estará online en ~2 minutos

#### Docker

```bash
git clone https://github.com/pauvalls/open-trader.git
cd open-trader
cp backend/.env.example backend/.env
# Edita backend/.env con tu configuración
docker-compose up -d
```

### 🎮 Uso del Agente AI

**Crear un Agente:**
```bash
curl -X POST https://tu-app.railway.app/agent/create/mi-agente \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "tu-cuenta-id",
    "symbols": ["ETH/USDT", "BTC/USDT"],
    "preset": "balanced",
    "kimi_api_key": "api-key-opcional-para-modo-ia"
  }'
```

**Control:**
```bash
# Iniciar
curl -X POST https://tu-app.railway.app/agent/control/mi-agente \
  -d '{"action": "start"}'

# Ver estado
curl https://tu-app.railway.app/agent/status/mi-agente
```

### 🧠 Cómo Funciona el Agente AI

**Modo 1: Estrategias Técnicas (Por defecto)**
- Monitorea el mercado cada 15 minutos
- Usa RSI + MACD + Bollinger Bands
- Ejecuta cuando 2/3 estrategias coinciden
- Sin IA - análisis técnico puro

**Modo 2: IA Mejorada (Opcional)**
- Mismo análisis técnico
- ADEMÁS: Envía datos a Kimi AI para validación adicional
- Solo opera cuando IA + estrategias coinciden
- Requiere `KIMI_API_KEY`

### 📁 Estructura

```
open-trader/
├── backend/           # FastAPI + lógica de trading
│   ├── app/
│   │   ├── routers/   # Endpoints API
│   │   ├── services/  # Mercado, alertas, agente AI
│   │   └── strategies/# RSI, MACD, Bollinger
│   ├── main.py
│   └── requirements.txt
├── Dockerfile
├── railway.json       # Configuración template Railway
└── docker-compose.yml
```

### 🔧 Configuración

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `DATABASE_URL` | URL PostgreSQL (Railway lo configura) | Auto |
| `KIMI_API_KEY` | API key de Moonshot AI | Opcional |
| `TELEGRAM_BOT_TOKEN` | Bot Telegram para alertas | Opcional |
| `DISCORD_WEBHOOK_URL` | Webhook Discord | Opcional |

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

## 🤝 Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

<div align="center">

**Made with ❤️ by Pau & Kimi**

</div>
