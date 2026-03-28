"""
AI Trading Agent Router

Endpoints to control and monitor the autonomous AI trading agent.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..services.agent_service import (
    AITradingAgent, AgentConfig, get_or_create_agent, 
    get_agent, list_agents, AgentStatus, save_agent_state
)
from ..services.paper_trading_service import PaperTradingService
from ..services.market_multi import MultiMarketService
from ..database import get_db
from ..routers.user_config import get_decrypted_api_key
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

router = APIRouter(prefix="/agent", tags=["AI Trading Agent"])

# Service dependencies
def get_trading_service():
    return PaperTradingService()

def get_market_service():
    return MultiMarketService()


# ============ Pydantic Models ============

class AgentCreateRequest(BaseModel):
    """Request to create/configure a trading agent"""
    account_id: str
    symbols: List[str] = Field(default=["ETH/USDT", "BTC/USDT"], 
                               description="Trading pairs to monitor")
    timeframe: str = Field(default="1h", description="Analysis timeframe")
    check_interval_minutes: int = Field(default=15, ge=5, le=1440,
                                        description="How often to check for signals")
    
    # Strategies
    use_rsi: bool = True
    use_macd: bool = True  
    use_bollinger: bool = True
    consensus_threshold: int = Field(default=2, ge=1, le=3,
                                     description="Min strategies needed to trade")
    
    # Risk Management
    max_position_size_usd: float = Field(default=1000.0, gt=0,
                                         description="Max $ per position")
    max_positions: int = Field(default=3, ge=1, le=10,
                               description="Max concurrent positions")
    max_daily_trades: int = Field(default=10, ge=1, le=100)
    stop_loss_pct: float = Field(default=5.0, ge=0.1, le=50)
    take_profit_pct: float = Field(default=10.0, ge=0.1, le=100)
    
    # AI Enhancement
    use_kimi_api: bool = False
    kimi_api_key: Optional[str] = None
    kimi_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class AgentControlRequest(BaseModel):
    """Control commands for the agent"""
    action: str = Field(..., pattern="^(start|stop|pause|resume)$",
                        description="Control action: start, stop, pause, resume")


class AgentConfigUpdate(BaseModel):
    """Update agent configuration (only provided fields are updated)"""
    symbols: Optional[List[str]] = None
    timeframe: Optional[str] = None
    check_interval_minutes: Optional[int] = Field(None, ge=5, le=1440)
    
    # Strategies
    use_rsi: Optional[bool] = None
    use_macd: Optional[bool] = None
    use_bollinger: Optional[bool] = None
    consensus_threshold: Optional[int] = Field(None, ge=1, le=3)
    
    # Risk Management
    max_position_size_usd: Optional[float] = Field(None, gt=0)
    max_positions: Optional[int] = Field(None, ge=1, le=10)
    max_daily_trades: Optional[int] = Field(None, ge=1, le=100)
    stop_loss_pct: Optional[float] = Field(None, ge=0.1, le=50)
    take_profit_pct: Optional[float] = Field(None, ge=0.1, le=100)
    
    # AI Enhancement
    use_kimi_api: Optional[bool] = None
    kimi_api_key: Optional[str] = None
    kimi_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class AgentStatusResponse(BaseModel):
    """Agent status response"""
    agent_id: str
    status: str
    is_running: bool
    config: Dict[str, Any]
    state: Dict[str, Any]
    recent_decisions: List[Dict[str, Any]]


class DecisionResponse(BaseModel):
    """Single trading decision"""
    symbol: str
    action: str
    confidence: float
    reason: str
    signals: Dict[str, str]
    timestamp: str
    kimi_enhanced: bool


# ============ Endpoints ============

@router.post("/create/{agent_id}", response_model=AgentStatusResponse)
async def create_agent(
    agent_id: str,
    request: AgentCreateRequest,
    trading_service: PaperTradingService = Depends(get_trading_service),
    market_service: MultiMarketService = Depends(get_market_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Create and configure a new AI trading agent.
    
    The agent will:
    - Monitor specified symbols for trading signals
    - Execute trades automatically based on strategy consensus
    - Respect risk management settings
    - Optionally use Kimi API for enhanced analysis
    
    Note: If kimi_api_key is not provided but use_kimi_api is True,
    the system will try to use the key stored in user configuration.
    """
    # Check if agent already exists and is running
    existing = get_agent(agent_id)
    if existing and existing.state.status == AgentStatus.RUNNING:
        raise HTTPException(400, f"Agent {agent_id} is already running. Stop it first.")
    
    # Get API key from user config if not provided in request
    api_key = request.kimi_api_key
    if request.use_kimi_api and not api_key:
        api_key = await get_decrypted_api_key(request.account_id, db)
        if api_key:
            print(f"🔑 Using stored API key for account {request.account_id}")
    
    # Create config
    config = AgentConfig(
        account_id=request.account_id,
        symbols=request.symbols,
        timeframe=request.timeframe,
        check_interval_minutes=request.check_interval_minutes,
        use_rsi=request.use_rsi,
        use_macd=request.use_macd,
        use_bollinger=request.use_bollinger,
        consensus_threshold=request.consensus_threshold,
        max_position_size_usd=request.max_position_size_usd,
        max_positions=request.max_positions,
        max_daily_trades=request.max_daily_trades,
        stop_loss_pct=request.stop_loss_pct,
        take_profit_pct=request.take_profit_pct,
        use_kimi_api=request.use_kimi_api,
        kimi_api_key=api_key,
        kimi_confidence_threshold=request.kimi_confidence_threshold
    )
    
    # Create agent
    agent = get_or_create_agent(agent_id, config, trading_service, market_service)
    
    # Save to database
    await save_agent_state(agent_id, agent)
    
    return {
        "agent_id": agent_id,
        "status": agent.state.status.value,
        "is_running": agent.state.status == AgentStatus.RUNNING,
        "config": agent.get_status()["config"],
        "state": agent.get_status()["state"],
        "recent_decisions": []
    }


@router.post("/control/{agent_id}", response_model=AgentStatusResponse)
async def control_agent(
    agent_id: str,
    request: AgentControlRequest
):
    """
    Control an existing agent: start, stop, pause, or resume.
    
    - **start**: Begin autonomous trading
    - **stop**: Completely stop the agent
    - **pause**: Stop trading but keep agent alive
    - **resume**: Resume trading after pause
    """
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} not found. Create it first.")
    
    if request.action == "start":
        if agent.state.status == AgentStatus.RUNNING:
            raise HTTPException(400, "Agent is already running")
        await agent.start()
        await save_agent_state(agent_id, agent)
        
    elif request.action == "stop":
        if agent.state.status == AgentStatus.IDLE:
            raise HTTPException(400, "Agent is not running")
        await agent.stop()
        await save_agent_state(agent_id, agent)
        
    elif request.action == "pause":
        if agent.state.status != AgentStatus.RUNNING:
            raise HTTPException(400, "Agent is not running")
        await agent.pause()
        await save_agent_state(agent_id, agent)
        
    elif request.action == "resume":
        if agent.state.status != AgentStatus.PAUSED:
            raise HTTPException(400, "Agent is not paused")
        await agent.resume()
        await save_agent_state(agent_id, agent)
    
    return {
        "agent_id": agent_id,
        "status": agent.state.status.value,
        "is_running": agent.state.status == AgentStatus.RUNNING,
        "config": agent.get_status()["config"],
        "state": agent.get_status()["state"],
        "recent_decisions": agent.get_status()["recent_decisions"]
    }


@router.get("/status/{agent_id}", response_model=AgentStatusResponse)
async def get_agent_status(agent_id: str):
    """Get detailed status of an agent"""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    status = agent.get_status()
    return {
        "agent_id": agent_id,
        "status": status["status"],
        "is_running": status["status"] == "running",
        "config": status["config"],
        "state": status["state"],
        "recent_decisions": status["recent_decisions"]
    }


@router.patch("/config/{agent_id}", response_model=AgentStatusResponse)
async def update_agent_config(
    agent_id: str,
    request: AgentConfigUpdate
):
    """
    Update configuration of an existing agent.
    
    Only provided fields are updated. The agent can be updated while running
    and changes take effect immediately.
    """
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} not found. Create it first.")
    
    # Update config fields that are provided
    update_data = request.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(agent.config, field):
            setattr(agent.config, field, value)
            print(f"📝 Updated {field} = {value}")
    
    return {
        "agent_id": agent_id,
        "status": agent.state.status.value,
        "is_running": agent.state.status == AgentStatus.RUNNING,
        "config": agent.get_status()["config"],
        "state": agent.get_status()["state"],
        "recent_decisions": agent.get_status()["recent_decisions"]
    }


@router.get("/decisions/{account_id}")
async def get_decision_history(
    account_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get permanent history of agent decisions for an account.
    
    - **limit**: Number of decisions to return (default 100, max 1000)
    - **offset**: Offset for pagination
    
    Returns all decisions (buy/sell/hold) with their context,
    including those that didn't result in trades.
    """
    from sqlalchemy import select, desc
    from ..database import AgentDecisionHistory
    
    result = await db.execute(
        select(AgentDecisionHistory)
        .where(AgentDecisionHistory.account_id == account_id)
        .order_by(desc(AgentDecisionHistory.timestamp))
        .limit(min(limit, 1000))
        .offset(offset)
    )
    
    decisions = result.scalars().all()
    
    return {
        "decisions": [
            {
                "id": d.id,
                "symbol": d.symbol,
                "action": d.action,
                "confidence": d.confidence,
                "reason": d.reason,
                "signals": d.signals_json,
                "consensus_threshold": d.consensus_threshold,
                "trade_executed": d.trade_executed,
                "order_id": d.order_id,
                "kimi_enhanced": d.kimi_enhanced,
                "kimi_confidence": d.kimi_confidence,
                "price_at_decision": d.price_at_decision,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None
            }
            for d in decisions
        ],
        "total": len(decisions),
        "account_id": account_id
    }


@router.get("/list")
async def list_all_agents():
    """List all created agents and their status"""
    agents = list_agents()
    return {
        "agents": [
            {"id": id, "status": status}
            for id, status in agents.items()
        ],
        "count": len(agents)
    }


@router.post("/test/{agent_id}", response_model=DecisionResponse)
async def test_agent_analysis(
    agent_id: str,
    symbol: Optional[str] = None
):
    """
    Test the agent's analysis on a symbol without executing trades.
    
    Returns what the agent would do right now for the given symbol.
    """
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    test_symbol = symbol or agent.config.symbols[0]
    
    # Get account positions
    from ..services.trading_service import PaperTradingService
    trading_service = PaperTradingService()
    account = await trading_service.get_account(agent.config.account_id)
    current_positions = {p['symbol']: p for p in account.get('positions', [])}
    
    # Analyze
    decision = await agent._analyze_symbol(test_symbol, current_positions)
    
    return {
        "symbol": decision.symbol,
        "action": decision.action.value,
        "confidence": decision.confidence,
        "reason": decision.reason,
        "signals": decision.signals,
        "timestamp": decision.timestamp.isoformat(),
        "kimi_enhanced": decision.kimi_analysis is not None
    }


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Stop and delete an agent"""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} not found")
    
    await agent.stop()
    
    # Remove from registry
    from ..services import agent_service
    if agent_id in agent_service._agents:
        del agent_service._agents[agent_id]
    
    return {"message": f"Agent {agent_id} deleted"}


# ============ Preset Configurations ============

@router.get("/presets/conservative")
async def get_conservative_preset():
    """Get a conservative trading preset config"""
    return {
        "name": "Conservative",
        "description": "Low risk, steady returns. Requires 3/3 strategies to agree.",
        "config": {
            "consensus_threshold": 3,
            "max_position_size_usd": 500,
            "max_positions": 2,
            "max_daily_trades": 5,
            "stop_loss_pct": 3,
            "take_profit_pct": 6,
            "check_interval_minutes": 30
        }
    }


@router.get("/presets/aggressive")
async def get_aggressive_preset():
    """Get an aggressive trading preset config"""
    return {
        "name": "Aggressive",
        "description": "Higher risk, more trades. 2/3 strategies needed.",
        "config": {
            "consensus_threshold": 2,
            "max_position_size_usd": 2000,
            "max_positions": 5,
            "max_daily_trades": 20,
            "stop_loss_pct": 8,
            "take_profit_pct": 15,
            "check_interval_minutes": 10
        }
    }


@router.get("/presets/ai-enhanced")
async def get_ai_enhanced_preset():
    """Get an AI-enhanced preset (requires Kimi API key)"""
    return {
        "name": "AI Enhanced",
        "description": "Uses Kimi API for additional analysis. Best results but slower.",
        "config": {
            "consensus_threshold": 2,
            "max_position_size_usd": 1000,
            "max_positions": 3,
            "max_daily_trades": 10,
            "stop_loss_pct": 5,
            "take_profit_pct": 10,
            "check_interval_minutes": 15,
            "use_kimi_api": True,
            "kimi_confidence_threshold": 0.75
        },
        "note": "Requires KIMI_API_KEY environment variable or api_key in request"
    }
