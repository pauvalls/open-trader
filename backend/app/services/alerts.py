"""Alert service for Telegram and Discord notifications"""

import os
import httpx
from typing import Optional
from datetime import datetime


class AlertService:
    """Service to send alerts via Telegram and Discord"""
    
    def __init__(self):
        # Telegram
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Discord
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    async def send_telegram(self, message: str) -> bool:
        """Send message via Telegram bot"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10)
                return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram alert: {e}")
            return False
    
    async def send_discord(self, message: str, embed: Optional[dict] = None) -> bool:
        """Send message via Discord webhook"""
        if not self.discord_webhook_url:
            return False
        
        payload = {"content": message}
        if embed:
            payload["embeds"] = [embed]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.discord_webhook_url, 
                    json=payload, 
                    timeout=10
                )
                return response.status_code == 204
        except Exception as e:
            print(f"Error sending Discord alert: {e}")
            return False
    
    async def send_signal_alert(
        self,
        strategy: str,
        symbol: str,
        action: str,
        price: float,
        extra_info: Optional[dict] = None
    ):
        """Send formatted signal alert to all configured channels"""
        
        # Determine emoji based on action
        emoji = "🟢" if action == "buy" else "🔴" if action == "sell" else "⚪"
        action_text = "COMPRAR" if action == "buy" else "VENDER" if action == "sell" else "MANTENER"
        
        # Telegram message
        telegram_msg = f"""
{emoji} *SEÑAL DE TRADING*

*Estrategia:* {strategy}
*Par:* {symbol}
*Acción:* {action_text}
*Precio:* ${price:,.6f}

_Timestamp:_ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        if extra_info:
            for key, value in extra_info.items():
                telegram_msg += f"\n*{key}:* {value}"
        
        # Discord embed
        color = 0x00FF00 if action == "buy" else 0xFF0000 if action == "sell" else 0x808080
        discord_embed = {
            "title": f"{emoji} Señal de Trading",
            "color": color,
            "fields": [
                {"name": "Estrategia", "value": strategy, "inline": True},
                {"name": "Par", "value": symbol, "inline": True},
                {"name": "Acción", "value": action_text, "inline": True},
                {"name": "Precio", "value": f"${price:,.6f}", "inline": True},
                {"name": "Timestamp", "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'), "inline": False}
            ],
            "footer": {"text": "Open Trader"}
        }
        
        if extra_info:
            for key, value in extra_info.items():
                discord_embed["fields"].append({
                    "name": key,
                    "value": str(value),
                    "inline": True
                })
        
        # Send to both
        await self.send_telegram(telegram_msg)
        await self.send_discord(f"Señal de trading: {strategy} - {symbol}", discord_embed)
    
    async def send_order_alert(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        pnl: Optional[float] = None
    ):
        """Send order execution alert"""
        
        emoji = "🟢" if side == "buy" else "🔴"
        side_text = "COMPRA" if side == "buy" else "VENTA"
        
        pnl_text = ""
        if pnl is not None:
            pnl_emoji = "📈" if pnl > 0 else "📉"
            pnl_text = f"\n*P&L:* {pnl_emoji} ${pnl:,.2f}"
        
        telegram_msg = f"""
{emoji} *ORDEN EJECUTADA*

*Par:* {symbol}
*Tipo:* {side_text}
*Cantidad:* {amount:,.6f}
*Precio:* ${price:,.6f}
*Total:* ${amount * price:,.2f}{pnl_text}

_Timestamp:_ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        await self.send_telegram(telegram_msg)
        
        # Discord embed
        color = 0x00FF00 if side == "buy" else 0xFF0000
        fields = [
            {"name": "Par", "value": symbol, "inline": True},
            {"name": "Tipo", "value": side_text, "inline": True},
            {"name": "Cantidad", "value": f"{amount:,.6f}", "inline": True},
            {"name": "Precio", "value": f"${price:,.6f}", "inline": True},
            {"name": "Total", "value": f"${amount * price:,.2f}", "inline": True}
        ]
        
        if pnl is not None:
            fields.append({
                "name": "P&L",
                "value": f"${pnl:,.2f}",
                "inline": True
            })
        
        discord_embed = {
            "title": f"{emoji} Orden Ejecutada",
            "color": color,
            "fields": fields,
            "footer": {"text": "Open Trader"}
        }
        
        await self.send_discord(f"Orden ejecutada: {symbol}", discord_embed)
