"""Bollinger Bands Strategy implementation"""

import pandas as pd
import numpy as np
from typing import Dict


class BollingerStrategy:
    """
    Estrategia basada en Bandas de Bollinger
    
    Señal de compra: Precio toca o cruza por debajo de la banda inferior
    Señal de venta: Precio toca o cruza por encima de la banda superior
    
    Se puede usar con confirmación de reversión (precio vuelve dentro de las bandas)
    """
    
    def __init__(self, params: Dict = None):
        self.params = params or {}
        self.period = self.params.get('period', 20)
        self.std_dev = self.params.get('std_dev', 2.0)
        self.use_confirmation = self.params.get('use_confirmation', True)
    
    def calculate_bollinger(self, prices: pd.Series) -> tuple:
        """Calcular bandas de Bollinger"""
        sma = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()
        upper = sma + (std * self.std_dev)
        lower = sma - (std * self.std_dev)
        
        # %B: posición relativa del precio entre las bandas
        percent_b = (prices - lower) / (upper - lower)
        
        return sma, upper, lower, percent_b
    
    def get_signal(self, df: pd.DataFrame) -> Dict:
        """Obtener señal actual"""
        if 'close' not in df.columns:
            raise ValueError("DataFrame debe tener columna 'close'")
        
        df = df.copy()
        df['sma'], df['upper'], df['lower'], df['percent_b'] = self.calculate_bollinger(df['close'])
        
        current_price = df['close'].iloc[-1]
        current_upper = df['upper'].iloc[-1]
        current_lower = df['lower'].iloc[-1]
        current_sma = df['sma'].iloc[-1]
        current_percent_b = df['percent_b'].iloc[-1]
        
        if pd.isna(current_upper) or pd.isna(current_lower):
            return {
                'action': 'hold',
                'sma': None,
                'upper': None,
                'lower': None,
                'percent_b': None,
                'price': current_price
            }
        
        prev_price = df['close'].iloc[-2]
        prev_lower = df['lower'].iloc[-2]
        prev_upper = df['upper'].iloc[-2]
        
        action = 'hold'
        
        if self.use_confirmation:
            # Esperar confirmación: precio estaba fuera y vuelve dentro
            # Señal de compra: estaba por debajo de lower y sube por encima
            if prev_price <= prev_lower and current_price > current_lower:
                action = 'buy'
            # Señal de venta: estaba por encima de upper y baja por debajo
            elif prev_price >= prev_upper and current_price < current_upper:
                action = 'sell'
        else:
            # Señales sin confirmación (más agresivo)
            if current_price <= current_lower:
                action = 'buy'
            elif current_price >= current_upper:
                action = 'sell'
        
        return {
            'action': action,
            'sma': round(current_sma, 4),
            'upper': round(current_upper, 4),
            'lower': round(current_lower, 4),
            'percent_b': round(current_percent_b, 4),
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
        df['sma'], df['upper'], df['lower'], df['percent_b'] = self.calculate_bollinger(df['close'])
        
        balance = initial_balance
        position = 0
        trades = []
        
        for i in range(self.period + 1, len(df)):
            price = df['close'].iloc[i]
            upper = df['upper'].iloc[i]
            lower = df['lower'].iloc[i]
            sma = df['sma'].iloc[i]
            
            prev_price = df['close'].iloc[i-1]
            prev_upper = df['upper'].iloc[i-1]
            prev_lower = df['lower'].iloc[i-1]
            
            if pd.isna(upper) or pd.isna(lower):
                continue
            
            # Determinar señal
            signal = None
            if self.use_confirmation:
                if prev_price <= prev_lower and price > lower:
                    signal = 'buy'
                elif prev_price >= prev_upper and price < upper:
                    signal = 'sell'
            else:
                if price <= lower:
                    signal = 'buy'
                elif price >= upper:
                    signal = 'sell'
            
            # Ejecutar señal
            if signal == 'buy' and position == 0:
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
                    'lower': lower,
                    'sma': sma
                })
            
            elif signal == 'sell' and position > 0:
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
                    'upper': upper,
                    'sma': sma
                })
                
                position = 0
        
        final_price = df['close'].iloc[-1]
        final_value = balance + (position * final_price)
        total_return = (final_value - initial_balance) / initial_balance * 100
        
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) <= 0 and 'pnl' in t]
        
        return {
            'strategy': 'Bollinger Bands',
            'params': {
                'period': self.period,
                'std_dev': self.std_dev,
                'use_confirmation': self.use_confirmation
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
