"""
User Configuration Router

Endpoints to save/load user preferences and settings including API keys.
"""

import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db, UserConfig

router = APIRouter(tags=["User Configuration"])


# Simple encryption for API keys (in production, use proper key management)
def _encrypt_key(key: str) -> str:
    """Simple XOR encryption with env secret - NOT for production use"""
    secret = os.getenv("ENCRYPTION_SECRET", "open-trader-default-secret-key-32chars")
    # Ensure secret is long enough
    secret = (secret * (len(key) // len(secret) + 1))[:len(key)]
    encrypted = ''.join(chr(ord(k) ^ ord(s)) for k, s in zip(key, secret))
    return encrypted.encode('utf-8', errors='ignore').hex()


def _decrypt_key(encrypted_hex: str) -> str:
    """Decrypt API key"""
    try:
        secret = os.getenv("ENCRYPTION_SECRET", "open-trader-default-secret-key-32chars")
        encrypted = bytes.fromhex(encrypted_hex).decode('utf-8', errors='ignore')
        secret = (secret * (len(encrypted) // len(secret) + 1))[:len(encrypted)]
        return ''.join(chr(ord(e) ^ ord(s)) for e, s in zip(encrypted, secret))
    except Exception:
        return ""


# ============ Pydantic Models ============

class UserConfigRequest(BaseModel):
    """Request to save user configuration"""
    kimi_api_key: Optional[str] = Field(None, description="Kimi API key (will be encrypted)")
    use_kimi_api: bool = Field(False, description="Whether to use Kimi API")
    agent_preset: Optional[str] = Field(None, pattern="^(conservative|balanced|aggressive|ai)$")
    agent_symbols: Optional[List[str]] = None
    agent_strategies: Optional[List[str]] = None
    agent_risk_config: Optional[Dict[str, Any]] = None
    language: Optional[str] = Field(None, pattern="^(es|en)$")
    tutorial_seen: Optional[bool] = None


class UserConfigResponse(BaseModel):
    """User configuration response (API key is NOT returned)"""
    account_id: str
    has_kimi_api_key: bool  # Only indicate if key exists, not the key itself
    use_kimi_api: bool
    agent_preset: str
    agent_symbols: List[str]
    agent_strategies: List[str]
    agent_risk_config: Optional[Dict[str, Any]]
    language: str
    tutorial_seen: bool
    updated_at: str


class ApiKeyResponse(BaseModel):
    """Response for API key operations"""
    success: bool
    message: str
    has_key: bool


# ============ Endpoints ============

@router.get("/{account_id}", response_model=UserConfigResponse)
async def get_config(account_id: str, db: AsyncSession = Depends(get_db)):
async def get_config(account_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get user configuration for an account.
    
    Note: The API key itself is NOT returned for security.
    Only a flag indicating if a key exists is returned.
    """
    result = await db.execute(select(UserConfig).where(UserConfig.account_id == account_id))
    config = result.scalar_one_or_none()
    
    if not config:
        # Return default config
        return UserConfigResponse(
            account_id=account_id,
            has_kimi_api_key=False,
            use_kimi_api=False,
            agent_preset="balanced",
            agent_symbols=["BTC/USDT", "ETH/USDT"],
            agent_strategies=["rsi", "macd", "bollinger"],
            agent_risk_config=None,
            language="es",
            tutorial_seen=False,
            updated_at=""
        )
    
    return UserConfigResponse(
        account_id=config.account_id,
        has_kimi_api_key=bool(config.kimi_api_key_encrypted),
        use_kimi_api=config.use_kimi_api,
        agent_preset=config.agent_preset,
        agent_symbols=config.agent_symbols or ["BTC/USDT", "ETH/USDT"],
        agent_strategies=config.agent_strategies or ["rsi", "macd", "bollinger"],
        agent_risk_config=config.agent_risk_config,
        language=config.language,
        tutorial_seen=config.tutorial_seen,
        updated_at=config.updated_at.isoformat() if config.updated_at else ""
    )


@router.post("/{account_id}", response_model=UserConfigResponse)
async def save_config(
    account_id: str,
    request: UserConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Save user configuration for an account.
    
    If kimi_api_key is provided, it will be encrypted and stored securely.
    The key is NEVER returned in any response.
    """
    result = await db.execute(select(UserConfig).where(UserConfig.account_id == account_id))
    config = result.scalar_one_or_none()
    
    if not config:
        config = UserConfig(account_id=account_id)
        db.add(config)
    
    # Update fields
    if request.kimi_api_key is not None:
        if request.kimi_api_key.strip():
            config.kimi_api_key_encrypted = _encrypt_key(request.kimi_api_key.strip())
        else:
            # Empty string means delete the key
            config.kimi_api_key_encrypted = None
    
    if request.use_kimi_api is not None:
        config.use_kimi_api = request.use_kimi_api
    
    if request.agent_preset is not None:
        config.agent_preset = request.agent_preset
    
    if request.agent_symbols is not None:
        config.agent_symbols = request.agent_symbols
    
    if request.agent_strategies is not None:
        config.agent_strategies = request.agent_strategies
    
    if request.agent_risk_config is not None:
        config.agent_risk_config = request.agent_risk_config
    
    if request.language is not None:
        config.language = request.language
    
    if request.tutorial_seen is not None:
        config.tutorial_seen = request.tutorial_seen
    
    await db.commit()
    await db.refresh(config)
    
    return UserConfigResponse(
        account_id=config.account_id,
        has_kimi_api_key=bool(config.kimi_api_key_encrypted),
        use_kimi_api=config.use_kimi_api,
        agent_preset=config.agent_preset,
        agent_symbols=config.agent_symbols or ["BTC/USDT", "ETH/USDT"],
        agent_strategies=config.agent_strategies or ["rsi", "macd", "bollinger"],
        agent_risk_config=config.agent_risk_config,
        language=config.language,
        tutorial_seen=config.tutorial_seen,
        updated_at=config.updated_at.isoformat() if config.updated_at else ""
    )


@router.delete("/{account_id}/api-key", response_model=ApiKeyResponse)
async def delete_api_key(account_id: str, db: AsyncSession = Depends(get_db)):
    """Delete the stored Kimi API key for an account"""
    result = await db.execute(select(UserConfig).where(UserConfig.account_id == account_id))
    config = result.scalar_one_or_none()
    
    if config:
        config.kimi_api_key_encrypted = None
        config.use_kimi_api = False
        await db.commit()
    
    return ApiKeyResponse(
        success=True,
        message="API key deleted successfully",
        has_key=False
    )


@router.get("/{account_id}/api-key", response_model=ApiKeyResponse)
async def check_api_key(account_id: str, db: AsyncSession = Depends(get_db)):
    """Check if an API key is configured (returns boolean only, never the key)"""
    result = await db.execute(select(UserConfig).where(UserConfig.account_id == account_id))
    config = result.scalar_one_or_none()
    
    has_key = bool(config and config.kimi_api_key_encrypted)
    
    return ApiKeyResponse(
        success=True,
        message="API key exists" if has_key else "No API key configured",
        has_key=has_key
    )


# Internal function to get decrypted API key for agent service
async def get_decrypted_api_key(account_id: str, db: AsyncSession) -> Optional[str]:
    """Get decrypted API key for internal use (agent service only)"""
    result = await db.execute(select(UserConfig).where(UserConfig.account_id == account_id))
    config = result.scalar_one_or_none()
    
    if config and config.kimi_api_key_encrypted:
        return _decrypt_key(config.kimi_api_key_encrypted)
    return None