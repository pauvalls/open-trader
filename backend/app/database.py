"""Database configuration"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, JSON
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/paper_trading.db")

engine = create_async_engine(DATABASE_URL, echo=False)
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
