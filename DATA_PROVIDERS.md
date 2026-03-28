# 📊 Alternativas Gratuitas para Datos de Velas (OHLCV)

## 🔴 Problema Actual
Railway está sirviendo versión 0.2.1 en vez de 0.3.0. El endpoint `/market/klines` existe en el código pero no en producción.

---

## ✅ Opciones Gratuitas Recomendadas

### 1. **Binance API** (ACTUAL - CCXT) ⭐ RECOMENDADA
```python
# Ya implementado vía CCXT
import ccxt.async_support as ccxt

exchange = ccxt.binance({'enableRateLimit': True})
ohlcv = await exchange.fetch_ohlcv('ETH/USDT', '1h', limit=100)
```
- ✅ Gratis, sin API key
- ✅ Alta disponibilidad (99.9%)
- ✅ Datos en tiempo real
- ✅ Límites: 1200 req/min
- ✅ Histórico completo

### 2. **CoinGecko API** (Alternativa)
```python
import requests

# Free tier: 10-30 calls/min
url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
params = {
    'vs_currency': 'usd',
    'days': '30',
    'interval': 'hourly'
}
response = requests.get(url, params=params)
prices = response.json()['prices']  # [timestamp, price]
```
- ✅ Gratis (10-30 calls/min)
- ✅ No requiere API key para tier básico
- ❌ Sin datos OHLCV completos (solo precio/volumen)
- ❌ Rate limits estrictos

### 3. **CryptoCompare API** (Alternativa)
```python
import requests

# Free tier: 100k calls/mes
url = "https://min-api.cryptocompare.com/data/v2/histohour"
params = {
    'fsym': 'ETH',
    'tsym': 'USD',
    'limit': 100,
    'api_key': 'TU_API_KEY'  # Opcional para tier gratuito
}
response = requests.get(url, params=params)
data = response.json()['Data']['Data']
```
- ✅ Gratis (100k calls/mes)
- ✅ Datos OHLCV completos
- ✅ API key opcional para uso básico
- ✅ WebSocket disponible

### 4. **Yahoo Finance** (yfinance)
```python
import yfinance as yf

# Para cripto en Yahoo
 ticker = yf.Ticker("ETH-USD")
 hist = ticker.history(period="30d", interval="1h")
```
- ✅ Gratis, sin API key
- ✅ Datos históricos extensos
- ❌ No es tiempo real (15min delay)
- ❌ Menos pares disponibles

### 5. **Bybit API** (Alternativa a Binance)
```python
import ccxt.async_support as ccxt

exchange = ccxt.bybit({'enableRateLimit': True})
ohlcv = await exchange.fetch_ohlcv('ETH/USDT', '1h', limit=100)
```
- ✅ Gratis, sin API key para datos públicos
- ✅ Buena alternativa si Binance falla
- ✅ Alta disponibilidad

### 6. **Kraken API**
```python
import ccxt.async_support as ccxt

exchange = ccxt.kraken({'enableRateLimit': True})
ohlcv = await exchange.fetch_ohlcv('ETH/USDT', '1h', limit=100)
```
- ✅ Exchange regulado (EEUU/EU)
- ✅ Gratis para datos públicos
- ❌ Menos pares que Binance

---

## 🎯 Solución Recomendada: Multi-Provider

Implementar fallback automático si un provider falla:

```python
class MultiMarketService:
    """Servicio con múltiples fuentes de datos"""
    
    PROVIDERS = [
        ('binance', ccxt.binance),
        ('bybit', ccxt.bybit),
        ('kraken', ccxt.kraken),
        ('kucoin', ccxt.kucoin),
    ]
    
    async def get_klines(self, symbol, timeframe, limit=100):
        for name, exchange_class in self.PROVIDERS:
            try:
                exchange = exchange_class({'enableRateLimit': True})
                ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                await exchange.close()
                return self._format_ohlcv(ohlcv)
            except Exception as e:
                print(f"{name} failed: {e}")
                continue
        return None
```

---

## 🔧 Fix para Railway Deploy

### Opción A: Forzar Redeploy
```bash
# En Railway Dashboard
1. Ve a https://railway.app/dashboard
2. Selecciona proyecto "open-trader"
3. Click en "Deployments"
4. Click "Redeploy" en el último commit
```

### Opción B: Variables de Entorno
Asegúrate de que estas variables estén configuradas:
```
NIXPACKS_PYTHON_VERSION=3.11
RAILWAY_DOCKERFILE_PATH=Dockerfile
```

### Opción C: Nuevo Servicio
Si el deploy sigue fallando, crear servicio nuevo:
```bash
# En Railway Dashboard
1. New Project → Deploy from GitHub repo
2. Selecciona pauvalls/open-trader
3. Railway detectará el Dockerfile automáticamente
```

---

## 📈 Comparativa de Fuentes de Datos

| Fuente | Gratis | Sin API Key | OHLCV | Real-time | Fiabilidad |
|--------|--------|-------------|-------|-----------|------------|
| **Binance** | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Bybit** | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Kraken** | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ |
| **CryptoCompare** | ✅ | ✅ | ✅ | ❌ (1min) | ⭐⭐⭐ |
| **CoinGecko** | ✅ | ✅ | ❌ | ❌ | ⭐⭐ |
| **Yahoo** | ✅ | ✅ | ✅ | ❌ (15min) | ⭐⭐⭐ |

---

## 🚀 Mejoras para el Dashboard

### 1. Gráfico con Múltiples Timeframes
```javascript
// Permitir cambiar entre 1m, 5m, 15m, 1h, 4h, 1d
// con datos de diferentes providers
```

### 2. Indicadores Overlay
```javascript
// Añadir al chart.js:
- Líneas de EMA (9, 21, 50)
- Volumen en sub-gráfico
- RSI como oscilador abajo
```

### 3. Datos de Múltiples Exchanges
```javascript
// Mostrar precio de Binance vs otros exchanges
// Alertar si hay divergencia > 1%
```

### 4. Fallback Automático
```javascript
// Si fetch de /market/klines falla,
// intentar con otro endpoint o provider
```
