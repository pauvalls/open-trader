"""
AI Trading Agent Service

Autonomous trading agent that:
1. Monitors market signals continuously
2. Makes trading decisions based on strategy consensus
3. Executes trades automatically via paper trading
4. Can integrate with external AI (Kimi API) for enhanced decisions
5. Includes risk management and position sizing
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random

from fastapi import BackgroundTasks
import httpx

from ..services.trading_service import PaperTradingService
from ..services.market_multi import MultiMarketService
from ..strategies.rsi_strategy import RSIStrategy
from ..strategies.macd_strategy import MACDStrategy
from ..strategies.bollinger_strategy import BollingerStrategy
from ..strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class TradeAction(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class AgentConfig:
    """Configuration for the AI Trading Agent"""
    account_id: str
    symbols: List[str] = field(default_factory=lambda: ["ETH/USDT", "BTC/USDT"])
    timeframe: str = "1h"
    check_interval_minutes: int = 15
    
    # Strategy weights
    use_rsi: bool = True
    use_macd: bool = True
    use_bollinger: bool = True
    consensus_threshold: int = 2  # Min strategies agreeing to trade
    
    # Risk management
    max_position_size_usd: float = 1000.0
    max_positions: int = 3
    max_daily_trades: int = 10
    stop_loss_pct: float = 5.0
    take_profit_pct: float = 10.0
    
    # AI Enhancement
    use_kimi_api: bool = False
    kimi_api_key: Optional[str] = None
    kimi_confidence_threshold: float = 0.7
    
    # Filters
    min_volume_24h: float = 1000000  # Min $1M volume
    exclude_symbols: List[str] = field(default_factory=list)


@dataclass
class TradeDecision:
    """Decision made by the AI agent"""
    symbol: str
    action: TradeAction
    confidence: float
    amount: float
    reason: str
    signals: Dict[str, str]
    timestamp: datetime
    kimi_analysis: Optional[str] = None


@dataclass
class AgentState:
    """Current state of the agent"""
    status: AgentStatus = AgentStatus.IDLE
    last_check: Optional[datetime] = None
    trades_today: int = 0
    daily_pnl: float = 0.0
    positions_opened: int = 0
    positions_closed: int = 0
    errors: List[str] = field(default_factory=list)
    last_decisions: List[TradeDecision] = field(default_factory=list)


class AITradingAgent:
    """
    Autonomous AI Trading Agent
    
    Features:
    - Multi-strategy signal aggregation
    - Configurable risk management
    - Optional Kimi API integration for enhanced analysis
    - Paper trading execution
    - Detailed logging and performance tracking
    """
    
    def __init__(
        self,
        config: AgentConfig,
        trading_service: PaperTradingService,
        market_service: MultiMarketService
    ):
        self.config = config
        self.trading_service = trading_service
        self.market_service = market_service
        self.state = AgentState()
        
        # Initialize strategies
        self.strategies = {}
        if config.use_rsi:
            self.strategies['rsi'] = RSIStrategy()
        if config.use_macd:
            self.strategies['macd'] = MACDStrategy()
        if config.use_bollinger:
            self.strategies['bollinger'] = BollingerStrategy()
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the autonomous trading agent"""
        if self._running:
            logger.warning("Agent already running")
            return
            
        self._running = True
        self.state.status = AgentStatus.RUNNING
        logger.info(f"🤖 AI Trading Agent started for account {self.config.account_id}")
        logger.info(f"   Symbols: {self.config.symbols}")
        logger.info(f"   Check interval: {self.config.check_interval_minutes}min")
        logger.info(f"   Strategies: {list(self.strategies.keys())}")
        
        self._task = asyncio.create_task(self._trading_loop())
        
    async def stop(self):
        """Stop the agent"""
        self._running = False
        self.state.status = AgentStatus.IDLE
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 AI Trading Agent stopped")
        
    async def pause(self):
        """Pause trading but keep monitoring"""
        self.state.status = AgentStatus.PAUSED
        logger.info("⏸️ AI Trading Agent paused")
        
    async def resume(self):
        """Resume trading"""
        self.state.status = AgentStatus.RUNNING
        logger.info("▶️ AI Trading Agent resumed")
        
    async def _trading_loop(self):
        """Main trading loop"""
        while self._running:
            try:
                if self.state.status == AgentStatus.RUNNING:
                    await self._scan_and_trade()
                    
                # Wait for next check
                await asyncio.sleep(self.config.check_interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                self.state.errors.append(f"{datetime.now()}: {str(e)}")
                self.state.status = AgentStatus.ERROR
                await asyncio.sleep(60)  # Wait 1 min on error
                
    async def _scan_and_trade(self):
        """Scan markets and execute trades"""
        self.state.last_check = datetime.now()
        
        # Reset daily counters if new day
        if self.state.last_check.hour == 0 and self.state.last_check.minute < 15:
            self.state.trades_today = 0
            self.state.daily_pnl = 0.0
            
        # Check if we can trade more today
        if self.state.trades_today >= self.config.max_daily_trades:
            logger.debug("Max daily trades reached")
            return
            
        # Get current positions
        account = await self.trading_service.get_account(self.config.account_id)
        current_positions = {p['symbol']: p for p in account.get('positions', [])}
        
        logger.info(f"🔍 Scanning {len(self.config.symbols)} symbols...")
        
        for symbol in self.config.symbols:
            if not self._running:
                break
                
            try:
                decision = await self._analyze_symbol(symbol, current_positions)
                
                if decision.action != TradeAction.HOLD and decision.confidence >= 0.6:
                    logger.info(f"🎯 {symbol}: {decision.action.value.upper()} "
                              f"(confidence: {decision.confidence:.2f})")
                    logger.info(f"   Reason: {decision.reason}")
                    
                    # Execute trade
                    await self._execute_decision(decision, current_positions)
                    self.state.last_decisions.append(decision)
                    
                    # Keep only last 50 decisions
                    if len(self.state.last_decisions) > 50:
                        self.state.last_decisions.pop(0)
                        
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                
    async def _analyze_symbol(
        self, 
        symbol: str, 
        current_positions: Dict
    ) -> TradeDecision:
        """
        Analyze a symbol and return trading decision
        """
        signals = {}
        buy_signals = 0
        sell_signals = 0
        
        # Get signals from each strategy
        for name, strategy in self.strategies.items():
            try:
                # Use async method from BaseStrategy
                if isinstance(strategy, BaseStrategy):
                    signal = await strategy.get_signal_async(symbol, self.config.timeframe, self.market_service)
                else:
                    # Fallback for legacy strategies
                    signal = await self._get_strategy_signal(strategy, symbol)
                signals[name] = signal
                
                if signal == 'buy':
                    buy_signals += 1
                elif signal == 'sell':
                    sell_signals += 1
                    
            except Exception as e:
                logger.warning(f"Strategy {name} failed for {symbol}: {e}")
                signals[name] = 'error'
                
        # Determine consensus
        total_strategies = len(self.strategies)
        consensus = 'hold'
        confidence = 0.5
        
        if buy_signals >= self.config.consensus_threshold:
            consensus = 'buy'
            confidence = buy_signals / total_strategies
        elif sell_signals >= self.config.consensus_threshold:
            consensus = 'sell'
            confidence = sell_signals / total_strategies
            
        # Check current position
        has_position = symbol in current_positions
        position_side = current_positions.get(symbol, {}).get('side', None)
        
        # Determine action
        action = TradeAction.HOLD
        reason = f"Signals: {signals} | Consensus: {consensus}"
        
        if consensus == 'buy' and not has_position:
            action = TradeAction.BUY
            reason = f"🟢 BUY signal: {buy_signals}/{total_strategies} strategies agree"
            
        elif consensus == 'sell':
            if has_position and position_side == 'long':
                action = TradeAction.SELL
                reason = f"🔴 SELL signal: {sell_signals}/{total_strategies} strategies agree"
            elif not has_position:
                # Could implement short selling here
                pass
                
        # Calculate position size
        amount = 0.0
        if action != TradeAction.HOLD:
            # Get current price
            price_data = await self.market_service.get_ticker(symbol)
            current_price = price_data.get('last', 0)
            
            if current_price > 0:
                # Calculate amount based on max position size
                amount = self.config.max_position_size_usd / current_price
                
        # Optional: Enhance with Kimi API
        kimi_analysis = None
        if self.config.use_kimi_api and self.config.kimi_api_key and action != TradeAction.HOLD:
            try:
                kimi_analysis = await self._get_kimi_analysis(symbol, signals, confidence)
                if kimi_analysis:
                    # Adjust confidence based on Kimi analysis
                    kimi_confidence = kimi_analysis.get('confidence', 0.5)
                    confidence = (confidence + kimi_confidence) / 2
                    reason += f" | Kimi: {kimi_analysis.get('recommendation', 'neutral')}"
            except Exception as e:
                logger.warning(f"Kimi API analysis failed: {e}")
                
        return TradeDecision(
            symbol=symbol,
            action=action,
            confidence=confidence,
            amount=amount,
            reason=reason,
            signals=signals,
            timestamp=datetime.now(),
            kimi_analysis=kimi_analysis
        )
        
    async def _get_strategy_signal(self, strategy, symbol: str) -> str:
        """
        Fallback method to get signal from legacy strategies
        """
        import pandas as pd
        
        candles = await self.market_service.get_candles(symbol, self.config.timeframe, limit=100)
        if not candles or len(candles) < 30:
            return 'hold'
        
        df = pd.DataFrame(candles)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        result = strategy.get_signal(df)
        return result.get('action', 'hold')
        
    async def _get_kimi_analysis(
        self, 
        symbol: str, 
        signals: Dict[str, str], 
        base_confidence: float
    ) -> Optional[Dict]:
        """
        Get enhanced analysis from Kimi API
        """
        if not self.config.kimi_api_key:
            return None
            
        # Get recent price data for context
        try:
            candles = await self.market_service.get_candles(
                symbol, self.config.timeframe, limit=20
            )
            
            # Format data for Kimi
            price_context = {
                "symbol": symbol,
                "timeframe": self.config.timeframe,
                "current_price": candles[-1]['close'] if candles else None,
                "price_change_24h": ((candles[-1]['close'] - candles[0]['open']) / candles[0]['open'] * 100) if candles else 0,
                "signals": signals,
                "base_confidence": base_confidence
            }
            
            prompt = f"""Analyze this trading opportunity for {symbol}:

Technical Signals:
{json.dumps(signals, indent=2)}

Market Context:
- Current Price: ${price_context['current_price']:.2f if price_context['current_price'] else 'N/A'}
- 24h Change: {price_context['price_change_24h']:.2f}%
- Base Confidence: {base_confidence:.2f}

Respond in JSON format:
{{
    "recommendation": "buy" | "sell" | "hold",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "risk_level": "low" | "medium" | "high"
}}"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.moonshot.cn/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.kimi_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "kimi-k2.5",
                        "messages": [
                            {"role": "system", "content": "You are a crypto trading analyst. Be concise."},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    return json.loads(content)
                    
        except Exception as e:
            logger.error(f"Kimi API error: {e}")
            
        return None
        
    async def _execute_decision(
        self, 
        decision: TradeDecision, 
        current_positions: Dict
    ):
        """Execute a trading decision"""
        symbol = decision.symbol
        
        if decision.action == TradeAction.BUY:
            # Check position limits
            if len(current_positions) >= self.config.max_positions:
                logger.warning(f"Max positions reached, skipping {symbol}")
                return
                
            # Execute buy order
            try:
                order = await self.trading_service.create_order(
                    account_id=self.config.account_id,
                    symbol=symbol,
                    side="buy",
                    amount=decision.amount
                )
                
                # Set bracket orders if configured
                if self.config.stop_loss_pct > 0 or self.config.take_profit_pct > 0:
                    await self._set_bracket_orders(symbol, order, decision)
                    
                self.state.trades_today += 1
                self.state.positions_opened += 1
                logger.info(f"✅ BUY executed: {decision.amount} {symbol}")
                
            except Exception as e:
                logger.error(f"Failed to execute buy: {e}")
                
        elif decision.action == TradeAction.SELL:
            # Execute sell (close position)
            position = current_positions.get(symbol)
            if position:
                try:
                    await self.trading_service.create_order(
                        account_id=self.config.account_id,
                        symbol=symbol,
                        side="sell",
                        amount=position['amount']
                    )
                    self.state.trades_today += 1
                    self.state.positions_closed += 1
                    logger.info(f"✅ SELL executed: {position['amount']} {symbol}")
                    
                except Exception as e:
                    logger.error(f"Failed to execute sell: {e}")
                    
    async def _set_bracket_orders(
        self, 
        symbol: str, 
        entry_order: Dict, 
        decision: TradeDecision
    ):
        """Set stop loss and take profit orders"""
        try:
            entry_price = entry_order.get('price', 0)
            if entry_price <= 0:
                return
                
            sl_price = entry_price * (1 - self.config.stop_loss_pct / 100)
            tp_price = entry_price * (1 + self.config.take_profit_pct / 100)
            
            # Note: This would need the advanced orders service
            logger.info(f"   Bracket: SL @ ${sl_price:.2f}, TP @ ${tp_price:.2f}")
            
        except Exception as e:
            logger.warning(f"Failed to set bracket orders: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "status": self.state.status.value,
            "config": {
                "symbols": self.config.symbols,
                "timeframe": self.config.timeframe,
                "check_interval": self.config.check_interval_minutes,
                "strategies": list(self.strategies.keys()),
                "max_positions": self.config.max_positions,
                "max_daily_trades": self.config.max_daily_trades,
                "use_kimi_api": self.config.use_kimi_api
            },
            "state": {
                "last_check": self.state.last_check.isoformat() if self.state.last_check else None,
                "trades_today": self.state.trades_today,
                "daily_pnl": self.state.daily_pnl,
                "positions_opened": self.state.positions_opened,
                "positions_closed": self.state.positions_closed,
                "recent_errors": self.state.errors[-5:]
            },
            "recent_decisions": [
                {
                    "symbol": d.symbol,
                    "action": d.action.value,
                    "confidence": d.confidence,
                    "reason": d.reason,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in self.state.last_decisions[-10:]
            ]
        }


# Global agent registry
_agents: Dict[str, AITradingAgent] = {}


def get_or_create_agent(
    agent_id: str,
    config: AgentConfig,
    trading_service: PaperTradingService,
    market_service: MultiMarketService
) -> AITradingAgent:
    """Get existing agent or create new one"""
    if agent_id not in _agents:
        _agents[agent_id] = AITradingAgent(config, trading_service, market_service)
    return _agents[agent_id]


def get_agent(agent_id: str) -> Optional[AITradingAgent]:
    """Get agent by ID"""
    return _agents.get(agent_id)


def list_agents() -> Dict[str, str]:
    """List all agent IDs and their status"""
    return {id: agent.state.status.value for id, agent in _agents.items()}


def stop_all_agents():
    """Stop all running agents"""
    for agent in _agents.values():
        asyncio.create_task(agent.stop())
