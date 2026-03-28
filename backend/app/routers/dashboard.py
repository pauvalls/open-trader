"""Dashboard router - HTML dashboard with charts and trading interface"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

router = APIRouter()

# Read the improved dashboard HTML from file
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard_v3.html")
with open(dashboard_path, "r", encoding="utf-8") as f:
    DASHBOARD_HTML = f.read()

# Keep original for reference
DASHBOARD_HTML_LEGACY = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Open Trader - Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 20px 0; border-bottom: 1px solid #1a1a2e; margin-bottom: 30px;
        }
        h1 {
            font-size: 2rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .status { display: flex; gap: 10px; }
        .status span {
            padding: 6px 12px; border-radius: 20px; font-size: 0.8rem;
        }
        .status .online { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid #10b981; }
        .status .paper { background: rgba(168, 85, 247, 0.1); color: #a855f7; border: 1px solid #a855f7; }
        
        .controls {
            display: flex; gap: 15px; flex-wrap: wrap; align-items: center;
            margin-bottom: 30px; padding: 20px; background: #12121a;
            border-radius: 12px; border: 1px solid #1a1a2e;
        }
        .control-group { display: flex; flex-direction: column; gap: 5px; }
        .control-group label { font-size: 0.75rem; color: #888; text-transform: uppercase; }
        select, input {
            background: #1a1a2e; color: #e0e0e0; border: 1px solid #333;
            padding: 10px 15px; border-radius: 8px; font-size: 0.9rem; min-width: 150px;
        }
        button {
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            color: white; border: none; padding: 10px 20px;
            border-radius: 8px; cursor: pointer; font-weight: 500;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.9; }
        button.secondary {
            background: #1a1a2e; border: 1px solid #333; color: #e0e0e0;
        }
        
        .grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }
        .card {
            background: #12121a; border: 1px solid #1a1a2e;
            border-radius: 12px; padding: 20px;
        }
        .card h3 {
            color: #888; font-size: 0.75rem; text-transform: uppercase;
            letter-spacing: 1px; margin-bottom: 10px;
        }
        .value { font-size: 2rem; font-weight: bold; }
        .value.positive { color: #10b981; }
        .value.negative { color: #ef4444; }
        .value.neutral { color: #00d4ff; }
        
        .chart-container {
            position: relative; height: 400px;
            background: #0d0d12; border-radius: 8px; padding: 15px;
        }
        .chart-grid {
            display: grid; grid-template-columns: 2fr 1fr; gap: 20px;
            margin-bottom: 30px;
        }
        @media (max-width: 1024px) { .chart-grid { grid-template-columns: 1fr; } }
        
        .signals {
            display: flex; gap: 10px; flex-wrap: wrap;
        }
        .signal {
            padding: 10px 16px; border-radius: 8px; font-size: 0.85rem;
            font-weight: 500; display: flex; align-items: center; gap: 8px;
        }
        .signal.buy { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid #10b981; }
        .signal.sell { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid #ef4444; }
        .signal.hold { background: rgba(107, 114, 128, 0.1); color: #6b7280; border: 1px solid #6b7280; }
        
        .trade-form {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px; margin-top: 15px;
        }
        
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #1a1a2e; }
        th { color: #888; font-weight: 500; }
        .price-up { color: #10b981; }
        .price-down { color: #ef4444; }
        
        #logs {
            font-family: 'Courier New', monospace; font-size: 0.75rem;
            max-height: 250px; overflow-y: auto; background: #0d0d12;
            padding: 15px; border-radius: 8px;
        }
        .log-entry { padding: 4px 0; border-bottom: 1px solid #1a1a2e; }
        .log-time { color: #666; }
        .log-buy { color: #10b981; }
        .log-sell { color: #ef4444; }
        
        .loading { text-align: center; padding: 40px; color: #666; }
        .refresh-indicator {
            display: inline-block; width: 8px; height: 8px;
            border-radius: 50%; background: #10b981; margin-left: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        .account-info {
            display: flex; gap: 10px; align-items: center;
        }
        #accountSelect { min-width: 250px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🔥 Open Trader</h1>
                <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Trading Algorítmico con Paper Trading</p>
            </div>
            <div class="status">
                <span class="online">● Online</span>
                <span class="paper">Paper Trading</span>
            </div>
        </header>

        <div class="controls">
            <div class="control-group">
                <label>Cuenta</label>
                <div class="account-info">
                    <select id="accountSelect">
                        <option value="">Seleccionar cuenta...</option>
                    </select>
                    <button class="secondary" onclick="createAccount()">➕ Nueva</button>
                </div>
            </div>
            
            <div class="control-group">
                <label>Par de Trading</label>
                <select id="symbolSelect" onchange="updateChart()">
                    <option value="BTC/USDT">BTC/USDT</option>
                    <option value="ETH/USDT" selected>ETH/USDT</option>
                    <option value="SOL/USDT">SOL/USDT</option>
                    <option value="AVAX/USDT">AVAX/USDT</option>
                    <option value="ARB/USDT">ARB/USDT</option>
                    <option value="OP/USDT">OP/USDT</option>
                    <option value="LINK/USDT">LINK/USDT</option>
                    <option value="UNI/USDT">UNI/USDT</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Timeframe</label>
                <select id="timeframeSelect" onchange="updateChart()">
                    <option value="15m">15 Minutos</option>
                    <option value="1h" selected>1 Hora</option>
                    <option value="4h">4 Horas</option>
                    <option value="1d">1 Día</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Estrategia</label>
                <select id="strategySelect">
                    <option value="consensus" selected>🎯 Consenso Multi</option>
                    <option value="rsi">📊 RSI</option>
                    <option value="macd">📈 MACD</option>
                    <option value="bollinger">〰️ Bollinger</option>
                </select>
            </div>
            
            <div class="control-group" style="margin-left: auto;">
                <label>Acciones</label>
                <div style="display: flex; gap: 10px;">
                    <button onclick="refreshAll()">🔄 Actualizar</button>
                    <button class="secondary" onclick="scanStrategies()">📡 Escanear</button>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>💰 Balance Total</h3>
                <div class="value neutral" id="totalBalance">-</div>
            </div>
            <div class="card">
                <h3>📈 P&L No Realizado</h3>
                <div class="value" id="totalPnL">-</div>
            </div>
            <div class="card">
                <h3>📊 Posiciones Abiertas</h3>
                <div class="value neutral" id="openPositions">-</div>
            </div>
            <div class="card">
                <h3>💵 Balance Disponible</h3>
                <div class="value neutral" id="availableBalance">-</div>
            </div>
        </div>

        <div class="chart-grid">
            <div class="card">
                <h3>📈 Gráfico de Precios <span class="refresh-indicator"></span></h3>
                <div class="chart-container">
                    <canvas id="priceChart"></canvas>
                </div>
            </div>
            <div class="card">
                <h3>🎯 Señales de Trading</h3>
                <div id="signals" style="margin-bottom: 20px;">
                    <div class="loading">Escaneando estrategias...</div>
                </div>
                <hr style="border: none; border-top: 1px solid #1a1a2e; margin: 20px 0;">
                <h3>📝 Ejecutar Orden</h3>
                <div class="trade-form">
                    <div class="control-group">
                        <label>Tipo</label>
                        <select id="tradeSide">
                            <option value="buy">🟢 Comprar</option>
                            <option value="sell">🔴 Vender</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label>Cantidad</label>
                        <input type="number" id="tradeAmount" placeholder="0.1" step="0.01" min="0">
                    </div>
                    <div class="control-group" style="display: flex; align-items: flex-end;">
                        <button onclick="executeTrade()" style="width: 100%;">🚀 Ejecutar</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>📋 Posiciones Abiertas</h3>
                <div id="positionsList">
                    <div class="loading">Cargando...</div>
                </div>
            </div>
            <div class="card">
                <h3>📜 Historial de Órdenes</h3>
                <div id="ordersList">
                    <div class="loading">Cargando...</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>📝 Logs en Tiempo Real</h3>
            <div id="logs"></div>
        </div>
    </div>

    <script>
        const API_BASE = '';
        let currentAccount = null;
        let logs = [];
        let priceChart = null;

        // Auto-refresh every 10 seconds
        setInterval(refreshAll, 10000);

        async function refreshAll() {
            await loadAccounts();
            if (currentAccount) {
                await loadAccountData(currentAccount);
                await loadOrders(currentAccount);
            }
            await scanStrategies();
            await updateChart();
        }

        async function loadAccounts() {
            // Check localStorage for saved account
            const savedAccount = localStorage.getItem('openTraderAccount');
            if (savedAccount && !currentAccount) {
                currentAccount = savedAccount;
            }
            
            // Load accounts from API
            try {
                const response = await fetch(`${API_BASE}/paper/accounts`);
                const accounts = await response.json();
                
                const select = document.getElementById('accountSelect');
                // Clear existing options except the first one
                while (select.options.length > 1) {
                    select.remove(1);
                }
                
                accounts.forEach(account => {
                    const option = document.createElement('option');
                    option.value = account.id;
                    option.text = `${account.id.slice(0, 8)}... ($${account.current_balance.toLocaleString()})`;
                    select.appendChild(option);
                    
                    // Auto-select if matches currentAccount
                    if (account.id === currentAccount) {
                        select.value = account.id;
                    }
                });
                
                if (currentAccount && select.value === currentAccount) {
                    await loadAccountData(currentAccount);
                    await loadOrders(currentAccount);
                }
            } catch (e) {
                console.error('Error loading accounts:', e);
            }
        }

        async function createAccount() {
            try {
                const response = await fetch(`${API_BASE}/paper/account`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({initial_balance: 10000})
                });
                const data = await response.json();
                currentAccount = data.id;
                localStorage.setItem('openTraderAccount', currentAccount);
                
                const select = document.getElementById('accountSelect');
                const option = document.createElement('option');
                option.value = data.id;
                option.text = `${data.id.slice(0, 8)}... ($${data.initial_balance.toLocaleString()})`;
                select.appendChild(option);
                select.value = data.id;
                
                addLog('system', `Cuenta creada: ${data.id.slice(0, 8)}...`);
                await loadAccountData(data.id);
            } catch (e) {
                addLog('error', `Error creando cuenta: ${e.message}`);
            }
        }

        async function loadAccountData(accountId) {
            try {
                const response = await fetch(`${API_BASE}/paper/account/${accountId}`);
                const data = await response.json();
                
                document.getElementById('totalBalance').textContent = 
                    `$${(data.total_value || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                
                const pnlElement = document.getElementById('totalPnL');
                const pnl = data.unrealized_pnl || 0;
                pnlElement.textContent = `$${pnl.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                pnlElement.className = 'value ' + (pnl >= 0 ? 'positive' : 'negative');
                
                document.getElementById('openPositions').textContent = data.open_positions || '0';
                document.getElementById('availableBalance').textContent = 
                    `$${(data.current_balance_usd || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                
                // Update account selector if not already there
                const select = document.getElementById('accountSelect');
                if (!Array.from(select.options).some(o => o.value === accountId)) {
                    const option = document.createElement('option');
                    option.value = accountId;
                    option.text = `${accountId.slice(0, 8)}... ($${data.total_value?.toFixed(0) || 0})`;
                    select.appendChild(option);
                    select.value = accountId;
                }
                
                // Load positions table
                const positionsHtml = data.positions?.length 
                    ? `<table>
                        <tr><th>Par</th><th>Side</th><th>Cantidad</th><th>Entry</th><th>Actual</th><th>P&L</th></tr>
                        ${data.positions.map(p => `
                            <tr>
                                <td><strong>${p.symbol}</strong></td>
                                <td class="${p.side === 'long' ? 'price-up' : 'price-down'}">${p.side.toUpperCase()}</td>
                                <td>${p.amount.toFixed(6)}</td>
                                <td>$${p.entry_price.toFixed(4)}</td>
                                <td>$${(p.current_price || p.entry_price).toFixed(4)}</td>
                                <td class="${(p.unrealized_pnl || 0) >= 0 ? 'price-up' : 'price-down'}">
                                    ${p.unrealized_pnl >= 0 ? '+' : ''}$${p.unrealized_pnl?.toFixed(2) || 0}
                                </td>
                            </tr>
                        `).join('')}
                       </table>`
                    : '<p style="color: #666; padding: 20px; text-align: center;">Sin posiciones abiertas</p>';
                document.getElementById('positionsList').innerHTML = positionsHtml;
                
            } catch (e) {
                addLog('error', `Error cargando cuenta: ${e.message}`);
            }
        }

        async function loadOrders(accountId) {
            try {
                const response = await fetch(`${API_BASE}/paper/orders/${accountId}?limit=10`);
                const data = await response.json();
                
                const ordersHtml = data?.length 
                    ? `<table>
                        <tr><th>Hora</th><th>Par</th><th>Tipo</th><th>Cantidad</th><th>Precio</th><th>Total</th><th>P&L</th></tr>
                        ${data.map(o => `
                            <tr>
                                <td>${new Date(o.created_at).toLocaleString()}</td>
                                <td><strong>${o.symbol}</strong></td>
                                <td class="${o.side === 'buy' ? 'price-up' : 'price-down'}">${o.side.toUpperCase()}</td>
                                <td>${o.amount.toFixed(6)}</td>
                                <td>$${o.price.toFixed(4)}</td>
                                <td>$${(o.amount * o.price).toFixed(2)}</td>
                                <td class="${(o.pnl || 0) >= 0 ? 'price-up' : 'price-down'}">
                                    ${o.pnl ? (o.pnl >= 0 ? '+' : '') + '$' + o.pnl.toFixed(2) : '-'}
                                </td>
                            </tr>
                        `).join('')}
                       </table>`
                    : '<p style="color: #666; padding: 20px; text-align: center;">Sin órdenes ejecutadas</p>';
                document.getElementById('ordersList').innerHTML = ordersHtml;
                
            } catch (e) {
                addLog('error', `Error cargando órdenes: ${e.message}`);
            }
        }

        async function scanStrategies() {
            const symbol = document.getElementById('symbolSelect').value;
            const signalsDiv = document.getElementById('signals');
            
            try {
                const response = await fetch(`${API_BASE}/strategies/scan?symbol=${encodeURIComponent(symbol)}`);
                const data = await response.json();
                
                const consensusClass = data.consensus;
                const emoji = consensusClass === 'buy' ? '🟢' : consensusClass === 'sell' ? '🔴' : '⚪';
                const text = consensusClass === 'buy' ? 'COMPRAR' : consensusClass === 'sell' ? 'VENDER' : 'MANTENER';
                
                signalsDiv.innerHTML = `
                    <div class="signal ${consensusClass}" style="font-size: 1.1rem; padding: 15px 20px;">
                        ${emoji} <strong>${symbol}:</strong> ${text}
                        <span style="margin-left: 15px; font-size: 0.8rem; opacity: 0.8;">
                            (RSI: ${data.individual_signals?.rsi || '-'}, 
                             MACD: ${data.individual_signals?.macd || '-'}, 
                             BB: ${data.individual_signals?.bollinger || '-'})
                        </span>
                    </div>
                    <div style="margin-top: 10px; color: #666; font-size: 0.8rem;">
                        Precio actual: <span class="neutral">$${data.price?.toFixed(4) || '-'}</span>
                    </div>
                `;
                
                if (data.consensus !== 'hold') {
                    addLog(data.consensus, `Señal ${data.consensus.toUpperCase()} detectada para ${symbol} @ $${data.price?.toFixed(4)}`);
                }
                
            } catch (e) {
                signalsDiv.innerHTML = '<div style="color: #ef4444;">Error escaneando estrategias</div>';
            }
        }

        async function updateChart() {
            const symbol = document.getElementById('symbolSelect').value;
            const timeframe = document.getElementById('timeframeSelect').value;
            const container = document.querySelector('.chart-container');
            
            // Show loading
            if (!priceChart) {
                container.innerHTML = '<div class="loading" id="chartLoading">📊 Cargando gráfico...</div><canvas id="priceChart" style="display:none;"></canvas>';
            }
            
            try {
                // Use /candles endpoint with query params to avoid URL encoding issues with /
                const response = await fetch(`${API_BASE}/market/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=100`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const result = await response.json();
                
                if (!result.data || result.data.length === 0) {
                    container.innerHTML = '<div class="loading">❌ No hay datos disponibles</div>';
                    return;
                }
                
                const candles = result.data;
                // Show only last 50 candles for cleaner chart
                const recentCandles = candles.slice(-50);
                
                const labels = recentCandles.map((c, i) => {
                    const date = new Date(c.timestamp);
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                });
                const prices = recentCandles.map(c => c.close);
                
                // Get provider info
                const providerInfo = result.provider ? ` via ${result.provider}` : '';
                
                // Remove loading, show canvas
                container.innerHTML = '<canvas id="priceChart"></canvas>';
                const ctx = document.getElementById('priceChart').getContext('2d');
                
                if (priceChart) {
                    priceChart.destroy();
                }
                
                // Calculate gradient color based on trend
                const startPrice = prices[0];
                const endPrice = prices[prices.length - 1];
                const isUp = endPrice >= startPrice;
                
                const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                if (isUp) {
                    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.3)');
                    gradient.addColorStop(1, 'rgba(16, 185, 129, 0)');
                } else {
                    gradient.addColorStop(0, 'rgba(239, 68, 68, 0.3)');
                    gradient.addColorStop(1, 'rgba(239, 68, 68, 0)');
                }
                
                priceChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: symbol + providerInfo,
                            data: prices,
                            borderColor: isUp ? '#10b981' : '#ef4444',
                            backgroundColor: gradient,
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3,
                            pointRadius: 0,
                            pointHoverRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            legend: { 
                                display: true,
                                labels: { color: '#888' }
                            },
                            tooltip: {
                                backgroundColor: '#1a1a2e',
                                titleColor: '#e0e0e0',
                                bodyColor: '#e0e0e0',
                                borderColor: '#333',
                                borderWidth: 1,
                                callbacks: {
                                    label: (context) => `Precio: $${context.parsed.y.toFixed(4)}`
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: '#1a1a2e' },
                                ticks: { 
                                    color: '#666', 
                                    maxTicksLimit: 8,
                                    maxRotation: 45
                                }
                            },
                            y: {
                                grid: { color: '#1a1a2e' },
                                ticks: { 
                                    color: '#666',
                                    callback: (value) => '$' + value.toFixed(2)
                                }
                            }
                        }
                    }
                });
                
            } catch (e) {
                console.error('Error loading chart:', e);
                container.innerHTML = `<div class="loading">
                    ❌ Error cargando gráfico<br>
                    <span style="font-size:0.8rem; color:#666;">${e.message}</span><br>
                    <button onclick="updateChart()" style="margin-top:10px; padding:5px 15px; font-size:0.8rem;">🔄 Reintentar</button>
                </div>`;
            }
        }

        async function executeTrade() {
            if (!currentAccount) {
                alert('Primero crea o selecciona una cuenta');
                return;
            }
            
            const symbol = document.getElementById('symbolSelect').value;
            const side = document.getElementById('tradeSide').value;
            const amount = parseFloat(document.getElementById('tradeAmount').value);
            
            if (!amount || amount <= 0) {
                alert('Ingresa una cantidad válida');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/paper/order`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        account_id: currentAccount,
                        symbol: symbol,
                        side: side,
                        amount: amount
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    addLog(side, `${side.toUpperCase()} ${amount} ${symbol} @ $${data.price.toFixed(4)}`);
                    await loadAccountData(currentAccount);
                    await loadOrders(currentAccount);
                } else {
                    addLog('error', `Error: ${data.detail || 'Unknown error'}`);
                }
            } catch (e) {
                addLog('error', `Error ejecutando orden: ${e.message}`);
            }
        }

        function addLog(type, message) {
            const time = new Date().toLocaleTimeString();
            let typeClass = 'log-time';
            if (type === 'buy') typeClass = 'log-buy';
            if (type === 'sell') typeClass = 'log-sell';
            if (type === 'error') typeClass = 'price-down';
            
            logs.unshift(`<span class="log-time">[${time}]</span> <span class="${typeClass}">${message}</span>`);
            if (logs.length > 100) logs.pop();
            
            document.getElementById('logs').innerHTML = logs.map(l => 
                `<div class="log-entry">${l}</div>`
            ).join('');
        }

        // Account selector change
        document.getElementById('accountSelect').addEventListener('change', (e) => {
            currentAccount = e.target.value;
            if (currentAccount) {
                localStorage.setItem('openTraderAccount', currentAccount);
                loadAccountData(currentAccount);
                loadOrders(currentAccount);
            }
        });

        // Initial load
        refreshAll();
    </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML with charts and trading interface"""
    return HTMLResponse(content=DASHBOARD_HTML)


@router.get("/api/status")
async def dashboard_status():
    """Get quick status for dashboard"""
    return {
        "status": "running",
        "mode": "paper_trading",
        "version": "0.5.0",
        "features": ["multi-dex", "advanced-orders", "realtime-charts", "multi-provider", "ai-agent", "i18n"]
    }
