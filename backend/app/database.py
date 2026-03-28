"""Database configuration"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, JSON
from datetime import datetime

def get_database_url():
    """Get database URL with proper driver conversion for Railway"""
    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/paper_trading.db")
    
    # Railway uses postgres:// but SQLAlchemy needs postgresql+asyncpg://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return url

DATABASE_URL = get_database_url()

# Configure engine based on database type
if "sqlite" in DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, echo=False)
else:
    # PostgreSQL with connection pooling for Railway
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class PaperAccount(Base):
    """Cuenta de paper trading"""
    __tablename__ = "paper_accounts"
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    initial_balance_usd = Column(Float, default=10000.0)
    current_balance_usd = Column(Float, default=10000.0)
    is_active = Column(Boolean, default=True)


class PaperPosition(Base):
    """Posiciones abiertas en paper trading"""
    __tablename__ = "paper_positions"
    
    id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)  # ej: ETH/USDC
    side = Column(String, nullable=False)  # buy o sell
    amount = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_open = Column(Boolean, default=True)
    
    # SL/TP tracking
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)
    stop_loss_pct = Column(Float, nullable=True)
    take_profit_pct = Column(Float, nullable=True)
    
    # SL/TP execution tracking
    sl_tp_triggered = Column(String, nullable=True)  # 'stop_loss', 'take_profit', or None
    sl_tp_triggered_at = Column(DateTime, nullable=True)


class PaperOrder(Base):
    """Órdenes ejecutadas en paper trading"""
    __tablename__ = "paper_orders"
    
    id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    order_type = Column(String, default="market")  # market, limit
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    status = Column(String, default="filled")  # pending, filled, cancelled
    pnl = Column(Float, nullable=True)  # Solo para cierres de posición
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # Para guardar señales de estrategia


class TradeJournal(Base):
    """Journal entries for trades - notes, reflections, lessons learned"""
    __tablename__ = "trade_journal"
    
    id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False)
    account_id = Column(String, nullable=False)
    
    # Journal content
    notes = Column(String, nullable=True)  # General notes about the trade
    emotions = Column(String(50), nullable=True)  # How did you feel?
    mistakes = Column(String, nullable=True)  # What went wrong?
    lessons = Column(String, nullable=True)  # What did you learn?
    strategy_rating = Column(Float, nullable=True)  # 1-10 rating
    
    # Tags for categorization
    tags = Column(String, nullable=True)  # Comma-separated tags
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserConfig(Base):
    """User configuration and settings - per account"""
    __tablename__ = "user_config"
    
    account_id = Column(String, primary_key=True)
    
    # AI Agent settings
    kimi_api_key_encrypted = Column(String, nullable=True)  # Encrypted API key
    use_kimi_api = Column(Boolean, default=False)
    
    # Default agent settings (JSON)
    agent_preset = Column(String, default="balanced")  # conservative, balanced, aggressive, ai
    agent_symbols = Column(JSON, default=list)  # ["BTC/USDT", "ETH/USDT"]
    agent_strategies = Column(JSON, default=list)  # ["rsi", "macd", "bollinger"]
    agent_risk_config = Column(JSON, nullable=True)  # Full risk config object
    
    # UI preferences
    language = Column(String, default="es")  # es, en
    tutorial_seen = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradingAgent(Base):
    """Agente de trading persistente"""
    __tablename__ = "trading_agents"
    
    id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False, index=True)
    
    # Status
    is_enabled = Column(Boolean, default=False)
    status = Column(String, default='stopped')  # running, stopped, paused, error
    
    # Config
    config_json = Column(JSON, default=dict)  # All agent config
    
    # Runtime state
    last_check_at = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)
    trades_today = Column(Integer, default=0)
    positions_opened = Column(Integer, default=0)
    positions_closed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentDecisionHistory(Base):
    """Historial permanente de decisiones del agente de trading"""
    __tablename__ = "agent_decision_history"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    account_id = Column(String, nullable=False, index=True)
    
    # Decision details
    symbol = Column(String, nullable=False)
    action = Column(String, nullable=False)  # buy, sell, hold
    confidence = Column(Float, nullable=False)
    reason = Column(String, nullable=True)
    
    # Strategy signals at decision time
    signals_json = Column(JSON, nullable=True)  # {rsi: 'buy', macd: 'hold', bollinger: 'buy'}
    consensus_threshold = Column(Integer, default=2)
    
    # Was a trade executed?
    trade_executed = Column(Boolean, default=False)
    order_id = Column(String, nullable=True)
    
    # Kimi API enhancement (if used)
    kimi_enhanced = Column(Boolean, default=False)
    kimi_confidence = Column(Float, nullable=True)
    
    # Market context
    price_at_decision = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


async def run_migrations():
    """Run migrations to add missing columns"""
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # Check if we're using PostgreSQL
        if "postgresql" in str(engine.url):
            # Add missing columns to paper_positions if they don't exist
            columns_to_add = [
                ("stop_loss_price", "FLOAT"),
                ("take_profit_price", "FLOAT"),
                ("stop_loss_pct", "FLOAT"),
                ("take_profit_pct", "FLOAT"),
                ("sl_tp_triggered", "VARCHAR(50)"),
                ("sl_tp_triggered_at", "TIMESTAMP"),
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    await conn.execute(text(f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'paper_positions' 
                                AND column_name = '{column_name}'
                            ) THEN
                                ALTER TABLE paper_positions ADD COLUMN {column_name} {column_type};
                            END IF;
                        END $$;
                    """))
                except Exception as e:
                    print(f"Migration note: {e}")
            
            # Add missing columns to paper_accounts if they don't exist
            account_columns = [
                ("is_active", "BOOLEAN DEFAULT TRUE"),
            ]
            
            for column_name, column_type in account_columns:
                try:
                    await conn.execute(text(f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'paper_accounts' 
                                AND column_name = '{column_name}'
                            ) THEN
                                ALTER TABLE paper_accounts ADD COLUMN {column_name} {column_type};
                            END IF;
                        END $$;
                    """))
                except Exception as e:
                    print(f"Migration note: {e}")
            
            print("✅ Database migrations completed")


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Run migrations for missing columns
    await run_migrations()


async def get_db():
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
