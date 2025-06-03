import numpy as np
import pandas as pd
from datetime import datetime

class TrendAnalyzer:
    def __init__(self, window=14):
        self.window = window
        
    def analyze(self, df, metal_type):
        """Анализирует данные и возвращает структурированный результат"""
        try:
            # Подготовка данных
            prices = df['price'].copy()
            if isinstance(prices, np.ndarray):
                prices = pd.Series(prices)
            
            # Расчет индикаторов
            indicators = {
                'rsi': float(self._calculate_rsi(prices).iloc[-1]),
                'ema_7': float(self._calculate_ema(prices, 7).iloc[-1]),
                'ema_21': float(self._calculate_ema(prices, 21).iloc[-1]),
                'macd': float(self._calculate_macd(prices)[0].iloc[-1]),
                'signal_line': float(self._calculate_macd(prices)[1].iloc[-1])
            }
            
            # Формирование рекомендации
            signals = self._generate_signals(indicators)
            main_signal = self._determine_main_signal(signals)
            
            return {
                'current_price': float(prices.iloc[-1]),
                'technical_analysis': {
                    'indicators': indicators,
                    'signals': signals,
                    'main_recommendation': main_signal
                },
                'metadata': {
                    'metal': metal_type,
                    'last_updated': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"Analysis error for {metal_type}: {str(e)}")
            return {
                'error': {
                    'message': str(e),
                    'metal': metal_type,
                    'timestamp': datetime.now().isoformat()
                },
                'current_price': float(df['price'].iloc[-1]) if 'price' in df else None
            }

    def _calculate_rsi(self, prices):
        """Расчет RSI с использованием pandas"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(self.window).mean()
        avg_loss = loss.rolling(self.window).mean()
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _calculate_ema(self, prices, period):
        """Расчет EMA с использованием pandas"""
        return prices.ewm(span=period, adjust=False).mean()

    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Расчет MACD"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal)
        return macd_line, signal_line

    def _generate_signals(self, indicators):
        """Генерация торговых сигналов"""
        signals = []
        
         # 1. RSI - самый важный индикатор
        if indicators['rsi'] < 30:
            signals.append({
                "priority": 1,
                "action": "BUY",
                "indicator": "RSI",
                "value": indicators['rsi'],
                "reason": "Сильная перепроданность"
            })
        elif indicators['rsi'] > 70:
            signals.append({
                "priority": 1,
                "action": "SELL",
                "indicator": "RSI", 
                "value": indicators['rsi'],
                "reason": "Сильная перекупленность"
            })
        
        # 2. MACD - средний приоритет
        macd_diff = indicators['macd'] - indicators['signal_line']
        if macd_diff > 0:
            signals.append({
                "priority": 2,
                "action": "BUY",
                "indicator": "MACD",
                "value": round(macd_diff, 2),
                "reason": "Бычье расхождение"
            })
        else:
            signals.append({
                "priority": 2,
                "action": "SELL",
                "indicator": "MACD",
                "value": round(abs(macd_diff), 2),
                "reason": "Медвежье расхождение"
            })
        
        # 3. EMA - низкий приоритет
        ema_diff = indicators['ema_7'] - indicators['ema_21']
        if ema_diff > 0:
            signals.append({
                "priority": 3,
                "action": "BUY",
                "indicator": "EMA",
                "value": round(ema_diff, 2),
                "reason": f"EMA7 > EMA21 на {round(ema_diff, 2)}"
            })
        else:
            signals.append({
                "priority": 3,
                "action": "SELL",
                "indicator": "EMA",
                "value": round(abs(ema_diff), 2),
                "reason": f"EMA7 < EMA21 на {round(abs(ema_diff), 2)}"
            })
        
        # по приоритету
        return sorted(signals, key=lambda x: x['priority'])
    
    def _determine_main_signal(self, signals):
        """Определяет главную рекомендацию на основе сигналов"""
        if not signals:
            return {
                'action': 'HOLD',
                'confidence': 0.5,
                'description': 'Недостаточно данных для анализа'
            }
        
        # Выбираем сигнал с максимальной уверенностью
        main_signal = max(signals, key=lambda x: x.get('confidence', 0))
        
        return {
            'action': main_signal.get('action', 'HOLD'),
            'confidence': main_signal.get('confidence', 0.5),
            'description': main_signal.get('reason', '')
        }