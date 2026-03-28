# Backend Open Trader

## Stack

- Python 3.11+
- FastAPI
- SQLite (paper trading) / PostgreSQL (producción)
- CCXT (datos de mercado)
- Web3.py (interacción blockchain)
- Pandas + TA-Lib (análisis técnico)

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Iniciar
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Paper Trading
- `POST /paper/account` - Crear cuenta demo
- `GET /paper/account/{id}` - Ver balance
- `POST /paper/order` - Ejecutar orden
- `GET /paper/orders` - Historial

### Market Data
- `GET /market/price/{symbol}` - Precio actual
- `GET /market/klines/{symbol}` - Velas históricas

### Estrategias
- `GET /strategies` - Listar estrategias
- `POST /strategies/{name}/backtest` - Backtest

## Configuración

Ver `.env.example` para todas las opciones.
