"""Advanced Trading Service

Soporta órdenes:
- MARKET: Ejecución inmediata al mejor precio
- LIMIT: Ejecución a precio específico o mejor
- STOP_LOSS: Se activa cuando el precio cruza el stop, ejecuta market
- STOP_LIMIT: Se activa cuando el precio cruza el stop, ejecuta limit

También incluye:
- Trailing stop loss
- Take profit (limit sell)
- Bracket orders (entry + stop + take profit)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable
from decimal import Decimal
from datetime import datetime
from enum import Enum
import asyncio
import json

from app.services.market import MarketService
from app.services.dex_service import get_dex_adapter, DEXConfig


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    TAKE_PROFIT = "take_profit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    TRIGGERED = "triggered"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Orden de trading"""
    id: str
    account_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: Decimal
    
    # Precios
    entry_price: Optional[Decimal] = None  # Para limit orders
    stop_price: Optional[Decimal] = None   # Para stop orders
    limit_price: Optional[Decimal] = None  # Para stop-limit
    
    # Trailing stop
    trailing_percent: Optional[Decimal] = None
    highest_price: Optional[Decimal] = None  # Para trailing stop en long
    lowest_price: Optional[Decimal] = None   # Para trailing stop en short
    
    # Estado
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: Decimal = Decimal("0")
    filled_price: Optional[Decimal] = None
    
    # Configuración DEX
    dex_id: str = "uniswap-arbitrum"
    fee_tier: int = 3000
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    # Callbacks
    on_fill: Optional[Callable] = None
    on_trigger: Optional[Callable] = None


@dataclass
class BracketOrder:
    """Orden bracket: entry + stop loss + take profit"""
    entry_order: Order
    stop_loss_order: Order
    take_profit_order: Order
    
    # Cuando se llena entry, se activan OCO (one-cancels-other) para SL y TP
    oco_active: bool = False


class AdvancedTradingService:
    """Servicio de trading avanzado con órdenes condicionales"""
    
    def __init__(self, market_service: MarketService):
        self.market = market_service
        self.orders: Dict[str, Order] = {}
        self.bracket_orders: Dict[str, BracketOrder] = {}
        self.monitoring_task = None
        self.price_cache: Dict[str, Decimal] = {}
    
    async def start_monitoring(self):
        """Inicia el loop de monitoreo de precios"""
        if self.monitoring_task is None or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Detiene el loop de monitoreo"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Loop principal que chequea condiciones de órdenes cada segundo"""
        while True:
            try:
                await self._check_orders()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error en monitor loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_orders(self):
        """Chequea todas las órdenes activas y ejecuta si se cumplen condiciones"""
        # Obtener precios actuales para todos los símbolos con órdenes
        symbols = set(o.symbol for o in self.orders.values() 
                     if o.status in [OrderStatus.OPEN, OrderStatus.PENDING])
        
        for symbol in symbols:
            try:
                price = await self.market.get_price(symbol)
                self.price_cache[symbol] = price
            except:
                continue
        
        # Procesar cada orden
        for order in list(self.orders.values()):
            if order.status not in [OrderStatus.OPEN, OrderStatus.PENDING]:
                continue
            
            current_price = self.price_cache.get(order.symbol)
            if current_price is None:
                continue
            
            should_execute = False
            execution_price = current_price
            
            # MARKET: Ejecutar inmediatamente
            if order.order_type == OrderType.MARKET:
                should_execute = True
            
            # LIMIT BUY: Ejecutar si precio <= limit
            elif order.order_type == OrderType.LIMIT and order.side == OrderSide.BUY:
                if order.entry_price and current_price <= order.entry_price:
                    should_execute = True
                    execution_price = min(current_price, order.entry_price)
            
            # LIMIT SELL: Ejecutar si precio >= limit
            elif order.order_type == OrderType.LIMIT and order.side == OrderSide.SELL:
                if order.entry_price and current_price >= order.entry_price:
                    should_execute = True
                    execution_price = max(current_price, order.entry_price)
            
            # STOP LOSS BUY (para cerrar short): Ejecutar si precio >= stop
            elif order.order_type == OrderType.STOP_LOSS and order.side == OrderSide.BUY:
                if order.stop_price and current_price >= order.stop_price:
                    should_execute = True
            
            # STOP LOSS SELL (para cerrar long): Ejecutar si precio <= stop
            elif order.order_type == OrderType.STOP_LOSS and order.side == OrderSide.SELL:
                if order.stop_price and current_price <= order.stop_price:
                    should_execute = True
            
            # TRAILING STOP SELL (long position)
            elif order.order_type == OrderType.TRAILING_STOP and order.side == OrderSide.SELL:
                if order.highest_price is None:
                    order.highest_price = current_price
                elif current_price > order.highest_price:
                    order.highest_price = current_price
                
                if order.trailing_percent and order.highest_price:
                    stop_level = order.highest_price * (Decimal("1") - order.trailing_percent / Decimal("100"))
                    if current_price <= stop_level:
                        should_execute = True
                        execution_price = current_price
            
            # TAKE PROFIT SELL: Ejecutar si precio >= target
            elif order.order_type == OrderType.TAKE_PROFIT and order.side == OrderSide.SELL:
                if order.entry_price and current_price >= order.entry_price:
                    should_execute = True
                    execution_price = max(current_price, order.entry_price)
            
            # Ejecutar si corresponde
            if should_execute:
                await self._execute_order(order, execution_price)
    
    async def _execute_order(self, order: Order, price: Decimal):
        """Ejecuta una orden (simulado para paper trading)"""
        order.status = OrderStatus.TRIGGERED
        
        if order.on_trigger:
            await order.on_trigger(order)
        
        # Simular ejecución (en live trading, aquí llamaríamos al DEX)
        order.status = OrderStatus.FILLED
        order.filled_amount = order.amount
        order.filled_price = price
        
        if order.on_fill:
            await order.on_fill(order)
        
        print(f"✅ Orden ejecutada: {order.side.value} {order.amount} {order.symbol} @ ${price}")
    
    # =========================================================================
    # MÉTODOS PÚBLICOS PARA CREAR ÓRDENES
    # =========================================================================
    
    async def create_market_order(
        self,
        account_id: str,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        dex_id: str = "uniswap-arbitrum"
    ) -> Order:
        """Crear orden de mercado (ejecución inmediata)"""
        order = Order(
            id=f"mkt_{datetime.utcnow().timestamp()}",
            account_id=account_id,
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            amount=amount,
            dex_id=dex_id,
            status=OrderStatus.OPEN
        )
        self.orders[order.id] = order
        await self.start_monitoring()
        return order
    
    async def create_limit_order(
        self,
        account_id: str,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        price: Decimal,
        dex_id: str = "uniswap-arbitrum",
        expires_hours: Optional[int] = None
    ) -> Order:
        """Crear orden limit (ejecución a precio específico)"""
        order = Order(
            id=f"lmt_{datetime.utcnow().timestamp()}",
            account_id=account_id,
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            amount=amount,
            entry_price=price,
            dex_id=dex_id,
            status=OrderStatus.OPEN,
            expires_at=datetime.utcnow() + __import__('datetime').timedelta(hours=expires_hours) if expires_hours else None
        )
        self.orders[order.id] = order
        await self.start_monitoring()
        return order
    
    async def create_stop_loss(
        self,
        account_id: str,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        stop_price: Decimal,
        dex_id: str = "uniswap-arbitrum"
    ) -> Order:
        """Crear stop loss (se activa al cruzar precio, ejecuta market)"""
        order = Order(
            id=f"sl_{datetime.utcnow().timestamp()}",
            account_id=account_id,
            symbol=symbol,
            side=side,
            order_type=OrderType.STOP_LOSS,
            amount=amount,
            stop_price=stop_price,
            dex_id=dex_id,
            status=OrderStatus.OPEN
        )
        self.orders[order.id] = order
        await self.start_monitoring()
        return order
    
    async def create_trailing_stop(
        self,
        account_id: str,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        trailing_percent: Decimal,
        dex_id: str = "uniswap-arbitrum"
    ) -> Order:
        """
        Crear trailing stop loss.
        
        Para ventas (cerrar long): El stop sube con el precio, manteniendo
        distance% por debajo del máximo alcanzado.
        
        Ejemplo: Compraste ETH a $2000, trailing 5%
        - ETH sube a $2200, stop se mueve a $2090 (2200 * 0.95)
        - ETH baja a $2100, no se activa
        - ETH baja a $2080, se activa y vende
        """
        order = Order(
            id=f"ts_{datetime.utcnow().timestamp()}",
            account_id=account_id,
            symbol=symbol,
            side=side,
            order_type=OrderType.TRAILING_STOP,
            amount=amount,
            trailing_percent=trailing_percent,
            dex_id=dex_id,
            status=OrderStatus.OPEN
        )
        self.orders[order.id] = order
        await self.start_monitoring()
        return order
    
    async def create_bracket_order(
        self,
        account_id: str,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        entry_price: Optional[Decimal],  # None para market entry
        stop_loss_price: Decimal,
        take_profit_price: Decimal,
        dex_id: str = "uniswap-arbitrum"
    ) -> BracketOrder:
        """
        Crear orden bracket completa:
        1. Entry (market o limit)
        2. Stop Loss (se activa si precio va en contra)
        3. Take Profit (se activa si precio va a favor)
        
        Cuando se llena entry, SL y TP se activan en modo OCO:
        - Si se activa SL, TP se cancela automáticamente
        - Si se activa TP, SL se cancela automáticamente
        """
        # Orden de entrada
        if entry_price:
            entry_order = await self.create_limit_order(
                account_id, symbol, side, amount, entry_price, dex_id
            )
        else:
            entry_order = await self.create_market_order(
                account_id, symbol, side, amount, dex_id
            )
        
        # Orden de stop loss (opuesta a entry)
        sl_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
        stop_loss_order = Order(
            id=f"br_sl_{datetime.utcnow().timestamp()}",
            account_id=account_id,
            symbol=symbol,
            side=sl_side,
            order_type=OrderType.STOP_LOSS,
            amount=amount,
            stop_price=stop_loss_price,
            dex_id=dex_id,
            status=OrderStatus.PENDING  # Espera a que entry se llene
        )
        
        # Orden de take profit (opuesta a entry, limit)
        tp_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
        take_profit_order = Order(
            id=f"br_tp_{datetime.utcnow().timestamp()}",
            account_id=account_id,
            symbol=symbol,
            side=tp_side,
            order_type=OrderType.TAKE_PROFIT,
            amount=amount,
            entry_price=take_profit_price,
            dex_id=dex_id,
            status=OrderStatus.PENDING
        )
        
        # Configurar OCO
        async def on_entry_fill(order: Order):
            """Cuando entry se llena, activar SL y TP"""
            stop_loss_order.status = OrderStatus.OPEN
            take_profit_order.status = OrderStatus.OPEN
            
            # Configurar cancelación mutua
            async def on_sl_fill(o: Order):
                take_profit_order.status = OrderStatus.CANCELLED
            
            async def on_tp_fill(o: Order):
                stop_loss_order.status = OrderStatus.CANCELLED
            
            stop_loss_order.on_fill = on_sl_fill
            take_profit_order.on_fill = on_tp_fill
        
        entry_order.on_fill = on_entry_fill
        
        # Guardar órdenes
        self.orders[stop_loss_order.id] = stop_loss_order
        self.orders[take_profit_order.id] = take_profit_order
        
        bracket = BracketOrder(
            entry_order=entry_order,
            stop_loss_order=stop_loss_order,
            take_profit_order=take_profit_order
        )
        self.bracket_orders[entry_order.id] = bracket
        
        return bracket
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancelar una orden pendiente"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status in [OrderStatus.PENDING, OrderStatus.OPEN]:
            order.status = OrderStatus.CANCELLED
            return True
        return False
    
    def get_open_orders(self, account_id: Optional[str] = None) -> List[Order]:
        """Obtener órdenes abiertas"""
        orders = [o for o in self.orders.values() 
                 if o.status in [OrderStatus.OPEN, OrderStatus.PENDING]]
        if account_id:
            orders = [o for o in orders if o.account_id == account_id]
        return orders
    
    def get_order_history(self, account_id: Optional[str] = None) -> List[Order]:
        """Obtener historial de órdenes"""
        orders = [o for o in self.orders.values() 
                 if o.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.EXPIRED]]
        if account_id:
            orders = [o for o in orders if o.account_id == account_id]
        return orders


# Instancia global
trading_service = AdvancedTradingService(MarketService())
