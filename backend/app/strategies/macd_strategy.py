"""MACD Strategy implementation"""

import pandas as pd
import numpy as np
from typing import Dict


class MACDStrategy:
    """
    Estrategia basada en MACD (Moving Average Convergence Divergence)
    
    Señal de compra: MACD cruza por encima de la señal
    Señal de venta: MACD cruza por debajo de la señal
    """
    
    def __init__(self, params: Dict = None):
        self.params = params or {}
        self.fast = self.params.get('fast', 12)
        self.slow = self.params.get('slow', 26)
        self.signal = self.params.get('signal', 9)
    
    def calculate_macd(self, prices: pd.Series) -> tuple:
        """Calcular MACD, señal y histograma"""
        exp1 = prices.ewm(span=self.fast, adjust=False).mean()
        exp2 = prices.ewm(span=self.slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=self.signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def get_signal(self, df: pd.DataFrame) -> Dict:
        """Obtener señal actual"""
        if 'close' not in df.columns:
            raise ValueError("DataFrame debe tener columna 'close'")
        
        df = df.copy()
        df['macd'], df['signal'], df['histogram'] = self.calculate_macd(df['close'])
        
        current_price = df['close'].iloc[-1]
        current_macd = df['macd'].iloc[-1]
        current_signal = df['signal'].iloc[-1]
        prev_macd = df['macd'].iloc[-2]
        prev_signal = df['signal'].iloc[-2]
        
        if pd.isna(current_macd) or pd.isna(current_signal):
            return {
                'action': 'hold',
                'macd': None,
                'signal': None,
                'histogram': None,
                'price': current_price
            }
        
        # Detectar cruces
        cross_up = prev_macd <= prev_signal and current_macd > current_signal
        cross_down = prev_macd >= prev_signal and current_macd < current_signal
        
        if cross_up:
            action = 'buy'
        elif cross_down:
            action = 'sell'
        else:
            action = 'hold'
        
        return {
            'action': action,
            'macd': round(current_macd, 4),
            'signal': round(current_signal, 4),
            'histogram': round(current_macd - current_signal, 4),
            'price': round(current_price, 6)
        }
    
    def backtest(
        self,
        df: pd.DataFrame,
        initial_balance: float = 10000.0,
        position_size: float = 0.1
    ) -> Dict:
        """Ejecutar backtest"""
        df = df.copy()
        df['macd'], df['signal'], df['histogram'] = self.calculate_macd(df['close'])
        
        balance = initial_balance
        position = 0
        trades = []
        
        for i in range(self.slow + self.signal, len(df)):
            price = df['close'].iloc[i]
            macd = df['macd'].iloc[i]
            signal = df['signal'].iloc[i]
            prev_macd = df['macd'].iloc[i-1]
            prev_signal = df['signal'].iloc[i-1]
            
            if pd.isna(macd) or pd.isna(signal):
                continue
            
            cross_up = prev_macd <= prev_signal and macd > signal
            cross_down = prev_macd >= prev_signal and macd < signal
            
            # Señal de compra
            if cross_up and position == 0:
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
                    'macd': macd,
                    'signal': signal
                })
            
            # Señal de venta
            elif cross_down and position > 0:
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
                    'macd': macd,
                    'signal': signal
                })
                
                position = 0
        
        final_price = df['close'].iloc[-1]
        final_value = balance + (position * final_price)
        total_return = (final_value - initial_balance) / initial_balance * 100
        
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) <= 0 and 'pnl' in t]
        
        return {
            'strategy': 'MACD',
            'params': {
                'fast': self.fast,
                'slow': self.slow,
                'signal': self.signal
            },
            'initial_balance': initial_balance,
            'final_balance': balance,
            'final_value_with_position': final_value,
            'total_return_pct': round(total_return, 2),
            'total_trades': len([t for t in trades if t['type'] == 'sell']),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(len(winning_trades) / max(len(winning_trades) + len(losing_trades), 1) * 100, 2),
            'trades': trades[-10:]
        }
