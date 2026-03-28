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


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
