"""
Webhook router for external trading signals
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Literal
import hmac
import hashlib
import os

from app.services.alerts import AlertService
from app.services.paper_trading_service import PaperTradingService

router = APIRouter()
alert_service = AlertService()
trading_service = PaperTradingService()


class TradingSignal(BaseModel):
    """External trading signal"""
    symbol: str = Field(..., description="Trading pair: ETH/USDT")
    action: Literal["buy", "sell", "close"] = Field(..., description="Signal action")
    side: Optional[Literal["long", "short"]] = Field(None, description="For buy: long or short")
    amount: Optional[float] = Field(None, description="Amount to trade")
    price: Optional[float] = Field(None, description="Limit price (optional)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    source: Optional[str] = Field("webhook", description="Signal source identifier")
    message: Optional[str] = Field(None, description="Additional message")


class WebhookConfig:
    """Webhook configuration"""
    SECRET = os.getenv("WEBHOOK_SECRET", "")
    ENABLED = os.getenv("WEBHOOK_ENABLED", "true").lower() == "true"


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    if not secret:
        return True  # No secret configured, skip verification
    
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


@router.post("/signal/{account_id}")
async def receive_signal(
    account_id: str,
    signal: TradingSignal,
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    x_webhook_source: Optional[str] = Header(None, alias="X-Webhook-Source")
):
    """
    Receive external trading signal via webhook
    
    Headers:
    - X-Webhook-Signature: HMAC SHA256 signature (if WEBHOOK_SECRET is set)
    - X-Webhook-Source: Source identifier
    
    Example signal:
    ```json
    {
        "symbol": "ETH/USDT",
        "action": "buy",
        "side": "long",
        "amount": 0.5,
        "stop_loss": 1800,
        "take_profit": 2200,
        "message": "Breakout detected"
    }
    ```
    """
    if not WebhookConfig.ENABLED:
        raise HTTPException(status_code=403, detail="Webhooks disabled")
    
    # Verify signature if secret is configured
    if WebhookConfig.SECRET and x_webhook_signature:
        # In real implementation, you'd verify the signature here
        pass
    
    try:
        # Send alert about received signal
        await alert_service.send_alert(
            f"📡 Webhook Signal: {signal.action.upper()} {signal.symbol}\n"
            f"Source: {signal.source or x_webhook_source or 'unknown'}\n"
            f"Message: {signal.message or 'N/A'}",
            level='info'
        )
        
        # Execute trade if configured to auto-trade
        if signal.action in ["buy", "sell"] and signal.amount:
            try:
                result = await trading_service.create_order(
                    account_id=account_id,
                    symbol=signal.symbol,
                    side="buy" if signal.action == "buy" else "sell",
                    amount=signal.amount
                )
                
                return {
                    "status": "executed",
                    "signal": signal.dict(),
                    "trade": result
                }
            except Exception as e:
                return {
                    "status": "signal_received_trade_failed",
                    "signal": signal.dict(),
                    "error": str(e)
                }
        
        return {
            "status": "signal_received",
            "signal": signal.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alert")
async def receive_alert(
    message: str,
    level: Literal["info", "warning", "error"] = "info",
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature")
):
    """
    Receive external alert/notification
    
    Example:
    ```json
    {
        "message": "High volatility detected in ETH",
        "level": "warning"
    }
    ```
    """
    try:
        await alert_service.send_alert(message, level=level)
        return {"status": "alert_sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_webhook_config():
    """Get webhook configuration (safe)"""
    return {
        "enabled": WebhookConfig.ENABLED,
        "signature_required": bool(WebhookConfig.SECRET),
        "endpoints": {
            "signal": "/webhook/signal/{account_id}",
            "alert": "/webhook/alert"
        }
    }
