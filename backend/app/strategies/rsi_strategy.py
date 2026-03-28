"""RSI Strategy implementation"""

import pandas as pd
import numpy as np
from typing import Dict, List


class RSIStrategy:
    """
    Estrategia basada en RSI (Relative Strength Index)
    
    Compra cuando RSI < oversold (sobrevendido)
    Vende cuando RSI > overbought (sobrecomprado)
    """
    
    def __init__(self, params: Dict = None):
        self.params = params or {}
        self.rsi_period = self.params.get('rsi_period', 14)
        self.oversold = self.params.get('oversold', 30)
        self.overbought = self.params.get('overbought', 70)
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calcular RSI"""
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_signal(self, df: pd.DataFrame) -> Dict:
        """
        Obtener señal actual
        
        Returns:
            {
                'action': 'buy' | 'sell' | 'hold',
                'rsi': float,
                'price': float
            }
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame debe tener columna 'close'")
        
        df = df.copy()
        df['rsi'] = self.calculate_rsi(df['close'])
        
        current_price = df['close'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        
        if pd.isna(current_rsi):
            return {'action': 'hold', 'rsi': None, 'price': current_price}
        
        if current_rsi < self.oversold:
            action = 'buy'
        elif current_rsi > self.overbought:
            action = 'sell'
        else:
            action = 'hold'
        
        return {
            'action': action,
            'rsi': round(current_rsi, 2),
            'price': round(current_price, 6)
        }
    
    def backtest(
        self, 
        df: pd.DataFrame, 
        initial_balance: float = 10000.0,
        position_size: float = 0.1  # 10% del balance por operación
    ) -> Dict:
        """
        Ejecutar backtest de la estrategia
        
        Returns:
            Dict con métricas de performance
        """
        df = df.copy()
        df['rsi'] = self.calculate_rsi(df['close'])
        
        balance = initial_balance
        position = 0  # Cantidad de cripto poseída
        trades = []
        
        for i in range(self.rsi_period, len(df)):
            price = df['close'].iloc[i]
            rsi = df['rsi'].iloc[i]
            
            if pd.isna(rsi):
                continue
            
            # Señal de compra
            if rsi < self.oversold and position == 0:
                amount_to_buy = (balance * position_size) / price
                cost = amount_to_buy * price
                balance -= cost
                position += amount_to_buy
                
                trades.append({
                    'type': 'buy',
                    'price': price,
                    'amount': amount_to_buy,
                    'cost': cost,
                    'balance': balance,
                    'rsi': rsi
                })
            
            # Señal de venta
            elif rsi > self.overbought and position > 0:
                revenue = position * price
                balance += revenue
                
                pnl = revenue - trades[-1]['cost'] if trades else 0
                
                trades.append({
                    'type': 'sell',
                    'price': price,
                    'amount': position,
                    'revenue': revenue,
                    'balance': balance,
                    'pnl': pnl,
                    'rsi': rsi
                })
                
                position = 0
        
        # Calcular valor final (balance + posición abierta)
        final_price = df['close'].iloc[-1]
        final_value = balance + (position * final_price)
        total_return = (final_value - initial_balance) / initial_balance * 100
        
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) <= 0 and 'pnl' in t]
        
        return {
            'strategy': 'RSI',
            'params': {
                'rsi_period': self.rsi_period,
                'oversold': self.oversold,
                'overbought': self.overbought
            },
            'initial_balance': initial_balance,
            'final_balance': balance,
            'final_value_with_position': final_value,
            'total_return_pct': round(total_return, 2),
            'total_trades': len([t for t in trades if t['type'] == 'sell']),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(len(winning_trades) / max(len(winning_trades) + len(losing_trades), 1) * 100, 2),
            'trades': trades[-10:]  # Solo últimas 10 para no saturar
        }
