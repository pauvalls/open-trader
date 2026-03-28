# Open Trader

Sistema de trading algorítmico de criptomonedas con soporte para paper trading y ejecución real en Uniswap V3.

## Características

- **Paper Trading**: Simula operaciones con dinero ficticio usando precios de mercado reales
- **Análisis Técnico**: RSI, MACD, medias móviles y más
- **Uniswap V3**: Integración lista para trading real en Arbitrum/Base
- **API REST**: Control total vía endpoints
- **Self-hosted**: Tú controlas tus claves y tu instancia

## Estructura

```
open-trader/
├── backend/           # FastAPI + lógica de trading
├── frontend/          # Dashboard (futuro)
├── contracts/         # Interacción con Uniswap V3
├── docker-compose.yml # Para self-hosting fácil
└── README.md
```

## Fase 1: Paper Trading

- Precios reales de Binance (free tier)
- Wallet virtual con saldo simulado
- Estrategias configurables
- Historial de operaciones

## Fase 2: Live Trading (futuro)

- Conexión a Uniswap V3
- Gestión de slippage y gas
- Protecciones de seguridad

## Instalación

Ver `backend/README.md` para instrucciones detalladas.
