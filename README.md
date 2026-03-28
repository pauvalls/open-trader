# Open Trader

Sistema de trading algorítmico de criptomonedas con soporte para paper trading y ejecución real en Uniswap V3.

**[English Documentation](README_EN.md)** | **[Changelog](CHANGELOG.md)** | **[Railway Deploy](RAILWAY.md)**

## ✨ Características

- **📊 Paper Trading**: Simula operaciones con dinero ficticio usando precios de mercado reales
- **📈 Estrategias**: RSI, MACD, Bollinger Bands + sistema de consenso multi-estrategia
- **🔔 Alertas**: Notificaciones en tiempo real vía Telegram y Discord
- **📱 Dashboard**: Interfaz web en tiempo real para monitorear operaciones
- **🔗 Uniswap V3**: Integración lista para trading real en Arbitrum/Base
- **🏠 Self-hosted**: Tú controlas tus claves y tu instancia

## 📁 Estructura

```
open-trader/
├── backend/           # FastAPI + lógica de trading
│   ├── app/
│   │   ├── routers/   # API endpoints (paper, market, strategies, dashboard)
│   │   ├── services/  # Market data, alerts
│   │   └── strategies/# RSI, MACD, Bollinger implementations
│   ├── main.py
│   └── requirements.txt
├── Dockerfile         # Build optimizado para producción (multi-stage)
├── railway.toml       # Configuración de Railway
├── docker-compose.yml # Para self-hosting fácil
├── CHANGELOG.md       # Historial de cambios
├── RAILWAY.md         # Guía de deploy en Railway
├── README.md          # Esta documentación (Español)
└── README_EN.md       # Documentación en Inglés
```

## 🚀 Quick Start

### Docker (Recomendado)

```bash
# Clonar y entrar
git clone https://github.com/pauvalls/open-trader.git
cd open-trader

# Configurar
cp backend/.env.example backend/.env
# Editar backend/.env con tus variables (ver Configuración)

# Levantar
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

### Python Local

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Editar .env

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Railway (Deploy con un click)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-url)

Ver [RAILWAY.md](RAILWAY.md) para instrucciones detalladas.

## 🌐 Acceso

Una vez levantado:

- **Dashboard**: http://localhost:8000/dashboard/
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/

## ⚙️ Configuración

Edita `backend/.env`:

```env
# API
DEBUG=true
SECRET_KEY=tu-clave-secreta-muy-larga

# Base de datos
DATABASE_URL=sqlite+aiosqlite:///./data/paper_trading.db

# Alertas (opcional pero recomendado)
TELEGRAM_BOT_TOKEN=tu-token-de-botfather
TELEGRAM_CHAT_ID=tu-chat-id
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Obtener credenciales de alertas:

**Telegram:**
1. Habla con [@BotFather](https://t.me/botfather)
2. Crea un bot nuevo (`/newbot`)
3. Copia el token
4. Envía un mensaje a tu bot
5. Ve a `https://api.telegram.org/bot[TU_TOKEN]/getUpdates` para ver tu chat_id

**Discord:**
1. En tu servidor: Server Settings → Integrations → Webhooks
2. New Webhook → Copy URL

## 📊 Estrategias Disponibles

| Estrategia | Descripción | Parámetros |
|------------|-------------|------------|
| **RSI** | Compra RSI<30, Vende RSI>70 | period, oversold, overbought |
| **MACD** | Cruce de MACD y señal | fast, slow, signal |
| **Bollinger** | Bandas de Bollinger | period, std_dev, use_confirmation |

### Consenso Multi-Estrategia

El endpoint `/strategies/scan` combina las 3 estrategias y genera una señal de consenso:
- **BUY**: 2+ estrategias indican compra
- **SELL**: 2+ estrategias indican venta
- **HOLD**: Sin consenso claro

## 🔌 API Endpoints Principales

### Paper Trading
```bash
# Crear cuenta
POST /paper/account
{"initial_balance": 10000}

# Ver cuenta
GET /paper/account/{id}

# Ejecutar orden
POST /paper/order
{
  "account_id": "uuid",
  "symbol": "ETH/USDT",
  "side": "buy",
  "amount": 0.5
}

# Historial
GET /paper/orders/{account_id}
```

### Estrategias
```bash
# Listar
GET /strategies

# Señal actual
GET /strategies/rsi/signal?symbol=ETH/USDT&timeframe=1h

# Backtest
POST /strategies/rsi/backtest
{
  "symbol": "ETH/USDT",
  "timeframe": "1h",
  "initial_balance": 10000,
  "strategy_params": {"rsi_period": 14}
}

# Scan multi-estrategia
GET /strategies/scan?symbol=BTC/USDT
```

### Market Data
```bash
# Precio actual
GET /market/price/ETH/USDT

# Velas históricas
GET /market/klines/ETH/USDT?timeframe=1h&limit=100

# Pares disponibles
GET /market/tickers
```

## 📱 Dashboard

Accede a `/dashboard/` para ver:
- Balance y P&L en tiempo real
- Posiciones abiertas
- Señales activas (auto-refresh cada 5s)
- Historial de órdenes
- Logs en tiempo real

## 🔔 Alertas

Las alertas se envían automáticamente cuando:
- Se detecta una señal de trading (buy/sell)
- Se ejecuta una orden
- Hay consenso multi-estrategia

Configura TELEGRAM_BOT_TOKEN y DISCORD_WEBHOOK_URL en `.env` para recibirlas.

## 🗺️ Roadmap

### Fase 1: Paper Trading ✅
- [x] Sistema de paper trading
- [x] Múltiples estrategias (RSI, MACD, Bollinger)
- [x] Alertas Telegram/Discord
- [x] Dashboard en tiempo real
- [ ] Machine Learning para estrategias

### Fase 2: Live Trading 🔄
- [ ] Integración Uniswap V3
- [ ] Gestión de gas y slippage
- [ ] Protecciones de seguridad (stop-loss, límites)
- [ ] Análisis on-chain

### Fase 3: Avanzado
- [ ] Portfolio rebalancing
- [ ] Arbitrage detection
- [ ] Yield farming automation

## ⚠️ Disclaimer

Este software es para fines educativos. El trading de criptomonedas implica riesgos significativos:
- Nunca inviertas más de lo que puedes perder
- Prueba exhaustivamente en paper trading antes de usar dinero real
- Revisa cada operación antes de confirmarla
- Yo (Kimi Claw) no soy asesor financiero

## 🤝 Contribuir

Este es un proyecto en desarrollo activo. Sugerencias y PRs son bienvenidos.

## 📄 Licencia

MIT - Úsalo bajo tu propia responsabilidad.
