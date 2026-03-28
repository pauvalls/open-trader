# Open Trader - Ideas para el Dashboard

## 🐛 Problema Actual: Gráfico no se ve
**Causa probable**: Railway está sirviendo una versión cacheada (aún muestra v0.2.1).
**Solución**: Esperar a que termine el deploy o hacer deploy manual en Railway dashboard.

---

## 🎨 Mejoras Sugeridas para el Dashboard

### 1. **Gráfico de Velas (Candlestick)**
```javascript
// Usar chartjs-chart-financial para velas reales
type: 'candlestick',
data: {
    datasets: [{
        data: candles.map(c => ({
            x: c.timestamp,
            o: c.open,
            h: c.high,
            l: c.low,
            c: c.close
        }))
    }]
}
```

### 2. **Indicadores Técnicos en el Gráfico**
- Líneas de RSI (oscilador abajo)
- Bandas de Bollinger (áreas sombreadas)
- Líneas MACD (histograma)
- Volumen (barras abajo)

### 3. **Panel de Órdenes Avanzadas**
```
┌─────────────────────────────────────┐
│  🎯 Bracket Order                    │
│  ─────────────────                   │
│  Entry:    [Market ▼] [$2000]       │
│  SL:       [5% ▼]   [$1900]        │
│  TP:       [10% ▼]  [$2200]        │
│  DEX:      [Uniswap Arbitrum ▼]    │
│           [🚀 Crear Bracket]        │
└─────────────────────────────────────┘
```

### 4. **Visualización de Órdenes en Gráfico**
- Marcar entry price con línea verde
- Marcar stop loss con línea roja
- Marcar take profit con línea verde claro
- Mostrar trailing stop dinámico

### 5. **Modo Oscuro/Claro Toggle**
```css
body.light {
    --bg: #ffffff;
    --card: #f5f5f5;
    --text: #1a1a1a;
}
```

### 6. **Sonidos de Alerta**
```javascript
const audio = new Audio('/static/alert.mp3');
if (signal === 'buy') audio.play();
```

### 7. **Notificaciones Desktop**
```javascript
if (Notification.permission === 'granted') {
    new Notification('Open Trader', {
        body: '🟢 Señal de COMPRA en ETH/USDT',
        icon: '/favicon.ico'
    });
}
```

### 8. **Gráfico de Balance Histórico**
```javascript
// Línea del balance a lo largo del tiempo
new Chart(ctx, {
    type: 'line',
    data: balanceHistory,
    options: { fill: true, tension: 0.4 }
});
```

### 9. **Heatmap de Posiciones**
- Colores verdes/rojos según P&L
- Tamaño proporcional a la posición
- Hover con detalles

### 10. **Mini Gráficos (Sparklines)**
```javascript
// En cada fila de la tabla de posiciones
<canvas class="sparkline" data-symbol="ETH/USDT"></canvas>
```

### 11. **Selección Múltiple de Estrategias**
```html
<input type="checkbox" id="useRSI" checked> RSI
<input type="checkbox" id="useMACD" checked> MACD
<input type="checkbox" id="useBB" checked> Bollinger
```

### 12. **Historial de Señales**
```
┌────────────────────────────────┐
│  📊 Historial de Señales        │
│  ─────────────────────          │
│  🟢 ETH/USDT @ $2005  14:32    │
│  🔴 BTC/USDT @ $65000 13:15    │
│  ⚪ SOL/USDT @ $145   12:08    │
└────────────────────────────────┘
```

### 13. **Comparador de Pares**
- Mostrar 4 gráficos pequeños al mismo tiempo
- BTC, ETH, SOL, AVAX
- Actualización simultánea

### 14. **Modo "Operador" (Fullscreen)**
```javascript
if (document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen();
}
```

### 15. **Atajos de Teclado**
```javascript
document.addEventListener('keydown', (e) => {
    if (e.key === 'b') executeTrade('buy');   // B = Buy
    if (e.key === 's') executeTrade('sell');  // S = Sell
    if (e.key === 'r') refreshAll();          // R = Refresh
});
```

---

## 🔧 Fixes Prioritarios

1. **Chart.js no carga**: Verificar CDN o usar versión local
2. **Auto-refresh**: Reducir a 5 segundos para datos más vivos
3. **Responsive**: Mejorar en móviles (stack layout vertical)
4. **Error handling**: Mostrar toast en vez de logs solo

---

## 🚀 Features de "Wow Factor"

### TradingView-style
- Herramientas de dibujo (líneas de tendencia)
- Zoom y pan en el gráfico
- Múltiples timeframes superpuestos

### AI Assistant Panel
```
┌─────────────────────────┐
│  🤖 Kimi Trader         │
│  ─────────────────      │
│  "ETH mostrando fuerza  │
│   alcista. RSI en 65,   │
│   considerar entrada    │
│   si rompe $2050"       │
└─────────────────────────┘
```

### Risk Calculator
```
Balance: $10,000
Riesgo:  2% ($200)
Stop:    $1800 (-10%)
Tamaño:  1.11 ETH
Leverage: 1x (spot)
```

### Social Trading
- Ver trades de otros usuarios (anónimo)
- Ranking de estrategias
- Copy trading entre cuentas

---

## 📱 Mobile App (PWA)

```javascript
// manifest.json
{
    "name": "Open Trader",
    "short_name": "OpenTrader",
    "start_url": "/dashboard/",
    "display": "standalone",
    "background_color": "#0a0a0f",
    "theme_color": "#00d4ff"
}
```

Service worker para:
- Funcionar offline (cachear últimos datos)
- Push notifications
- Background sync

---

## ¿Cuál quieres implementar primero?

Mi top 3:
1. **Fix del gráfico** (prioridad máxima)
2. **Visualización de órdenes en gráfico** (stop loss, entry, take profit)
3. **Panel de bracket orders** (UI simple para crear entry+sl+tp)
