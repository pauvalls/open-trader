"""Dashboard router - HTML dashboard and real-time updates"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

# Simple HTML dashboard (no templates needed for now)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Open Trader Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #1a1a2e;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-top: 10px;
        }
        .status.active {
            background: rgba(0, 212, 255, 0.1);
            color: #00d4ff;
            border: 1px solid #00d4ff;
        }
        .status.paper {
            background: rgba(123, 44, 191, 0.1);
            color: #a855f7;
            border: 1px solid #a855f7;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #12121a;
            border: 1px solid #1a1a2e;
            border-radius: 12px;
            padding: 20px;
        }
        .card h3 {
            color: #888;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .value {
            font-size: 2rem;
            font-weight: bold;
        }
        .value.positive { color: #10b981; }
        .value.negative { color: #ef4444; }
        .value.neutral { color: #00d4ff; }
        .signals {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .signal {
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .signal.buy {
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            border: 1px solid #10b981;
        }
        .signal.sell {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border: 1px solid #ef4444;
        }
        .signal.hold {
            background: rgba(107, 114, 128, 0.1);
            color: #6b7280;
            border: 1px solid #6b7280;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #1a1a2e;
        }
        th {
            color: #888;
            font-weight: 500;
            font-size: 0.85rem;
        }
        .price-up { color: #10b981; }
        .price-down { color: #ef4444; }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        #logs {
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            max-height: 300px;
            overflow-y: auto;
            background: #0d0d12;
            padding: 15px;
            border-radius: 8px;
        }
        .log-entry {
            padding: 4px 0;
            border-bottom: 1px solid #1a1a2e;
        }
        .log-time { color: #666; }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        button {
            background: #1a1a2e;
            color: #e0e0e0;
            border: 1px solid #333;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        button:hover {
            background: #252538;
            border-color: #00d4ff;
        }
        .account-selector {
            margin-bottom: 20px;
        }
        select, input {
            background: #1a1a2e;
            color: #e0e0e0;
            border: 1px solid #333;
            padding: 10px;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        .refresh-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            margin-left: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔥 Open Trader</h1>
            <span class="status active">● Online</span>
            <span class="status paper">Paper Trading</span>
        </header>

        <div class="controls">
            <button onclick="refreshAll()">🔄 Refrescar Todo</button>
            <button onclick="scanStrategies()">📊 Escanear Estrategias</button>
            <button onclick="createAccount()">➕ Nueva Cuenta</button>
        </div>

        <div class="account-selector">
            <label>Cuenta: </label>
            <select id="accountSelect">
                <option value="">Seleccionar cuenta...</option>
            </select>
        </div>

        <div class="grid">
            <div class="card">
                <h3>💰 Balance Total</h3>
                <div class="value neutral" id="totalBalance">-</div>
            </div>
            <div class="card">
                <h3>📈 P&L Total</h3>
                <div class="value" id="totalPnL">-</div>
            </div>
            <div class="card">
                <h3>📊 Posiciones Abiertas</h3>
                <div class="value neutral" id="openPositions">-</div>
            </div>
        </div>

        <div class="card">
            <h3>🎯 Señales Activas <span class="refresh-indicator"></span></h3>
            <div class="signals" id="signals">
                <div class="loading">Escaneando estrategias...</div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>📋 Posiciones</h3>
                <div id="positionsList">
                    <div class="loading">Cargando...</div>
                </div>
            </div>
            <div class="card">
                <h3>📜 Últimas Órdenes</h3>
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

        // Auto-refresh every 5 seconds
        setInterval(refreshAll, 5000);

        async function refreshAll() {
            await loadAccounts();
            if (currentAccount) {
                await loadAccountData(currentAccount);
                await loadOrders(currentAccount);
            }
            await scanStrategies();
            addLog('Datos actualizados');
        }

        async function loadAccounts() {
            // For now, we'll use a simple approach - in production you'd list accounts
            // This is a placeholder - in real implementation, you'd have an endpoint to list accounts
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
                
                const select = document.getElementById('accountSelect');
                const option = document.createElement('option');
                option.value = data.id;
                option.text = `Cuenta ${data.id.slice(0, 8)}... ($${data.initial_balance})`;
                select.appendChild(option);
                select.value = data.id;
                
                addLog(`Cuenta creada: ${data.id.slice(0, 8)}...`);
                await loadAccountData(data.id);
            } catch (e) {
                addLog(`Error creando cuenta: ${e.message}`);
            }
        }

        async function loadAccountData(accountId) {
            try {
                const response = await fetch(`${API_BASE}/paper/account/${accountId}`);
                const data = await response.json();
                
                document.getElementById('totalBalance').textContent = 
                    `$${data.total_value?.toLocaleString('en-US', {minimumFractionDigits: 2}) || '-'}`;
                
                const pnlElement = document.getElementById('totalPnL');
                pnlElement.textContent = data.unrealized_pnl 
                    ? `$${data.unrealized_pnl.toLocaleString('en-US', {minimumFractionDigits: 2})}`
                    : '-';
                pnlElement.className = 'value ' + (data.unrealized_pnl >= 0 ? 'positive' : 'negative');
                
                document.getElementById('openPositions').textContent = data.open_positions || '0';
                
                // Load positions table
                const positionsHtml = data.positions?.length 
                    ? `<table>
                        <tr><th>Par</th><th>Side</th><th>Cantidad</th><th>Entry</th><th>P&L</th></tr>
                        ${data.positions.map(p => `
                            <tr>
                                <td>${p.symbol}</td>
                                <td>${p.side}</td>
                                <td>${p.amount.toFixed(4)}</td>
                                <td>$${p.entry_price.toFixed(4)}</td>
                                <td class="${p.unrealized_pnl >= 0 ? 'price-up' : 'price-down'}">
                                    $${p.unrealized_pnl?.toFixed(2) || 0}
                                </td>
                            </tr>
                        `).join('')}
                       </table>`
                    : '<p style="color: #666; padding: 20px;">Sin posiciones abiertas</p>';
                document.getElementById('positionsList').innerHTML = positionsHtml;
                
            } catch (e) {
                addLog(`Error cargando cuenta: ${e.message}`);
            }
        }

        async function loadOrders(accountId) {
            try {
                const response = await fetch(`${API_BASE}/paper/orders/${accountId}?limit=10`);
                const data = await response.json();
                
                const ordersHtml = data?.length 
                    ? `<table>
                        <tr><th>Hora</th><th>Par</th><th>Tipo</th><th>Cantidad</th><th>Precio</th><th>P&L</th></tr>
                        ${data.map(o => `
                            <tr>
                                <td>${new Date(o.created_at).toLocaleTimeString()}</td>
                                <td>${o.symbol}</td>
                                <td class="${o.side === 'buy' ? 'price-up' : 'price-down'}">${o.side.toUpperCase()}</td>
                                <td>${o.amount.toFixed(4)}</td>
                                <td>$${o.price.toFixed(4)}</td>
                                <td class="${(o.pnl || 0) >= 0 ? 'price-up' : 'price-down'}">
                                    ${o.pnl ? '$' + o.pnl.toFixed(2) : '-'}
                                </td>
                            </tr>
                        `).join('')}
                       </table>`
                    : '<p style="color: #666; padding: 20px;">Sin órdenes</p>';
                document.getElementById('ordersList').innerHTML = ordersHtml;
                
            } catch (e) {
                addLog(`Error cargando órdenes: ${e.message}`);
            }
        }

        async function scanStrategies() {
            const symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT'];
            const signalsDiv = document.getElementById('signals');
            
            try {
                const results = await Promise.all(
                    symbols.map(async (symbol) => {
                        try {
                            const response = await fetch(`${API_BASE}/strategies/scan?symbol=${encodeURIComponent(symbol)}`);
                            return {symbol, data: await response.json()};
                        } catch (e) {
                            return {symbol, error: e.message};
                        }
                    })
                );
                
                signalsDiv.innerHTML = results.map(r => {
                    if (r.error) return '';
                    const signalClass = r.data.consensus;
                    const emoji = signalClass === 'buy' ? '🟢' : signalClass === 'sell' ? '🔴' : '⚪';
                    return `<div class="signal ${signalClass}">${emoji} ${r.symbol}: ${signalClass.toUpperCase()}</div>`;
                }).join('') || '<div style="color: #666;">Sin señales activas</div>';
                
            } catch (e) {
                signalsDiv.innerHTML = '<div style="color: #ef4444;">Error escaneando</div>';
            }
        }

        function addLog(message) {
            const time = new Date().toLocaleTimeString();
            logs.unshift(`<span class="log-time">[${time}]</span> ${message}`);
            if (logs.length > 50) logs.pop();
            document.getElementById('logs').innerHTML = logs.map(l => 
                `<div class="log-entry">${l}</div>`
            ).join('');
        }

        // Account selector change
        document.getElementById('accountSelect').addEventListener('change', (e) => {
            currentAccount = e.target.value;
            if (currentAccount) {
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
    """Serve the dashboard HTML"""
    return HTMLResponse(content=DASHBOARD_HTML)


@router.get("/api/status")
async def dashboard_status():
    """Get quick status for dashboard"""
    return {
        "status": "running",
        "mode": "paper_trading",
        "version": "0.1.0"
    }
