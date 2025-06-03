import pandas as pd
from datetime import datetime, timedelta

def get_test_data():
    dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
    test_data = {
        'Au': {
            'current_price': 8372.41,
            'technical_analysis': {
                'indicators': {
                    'rsi': 45.6,
                    'ema_7': 8400.12,
                    'ema_21': 8350.34,
                    'macd': -12.34,
                    'signal_line': -10.12
                },
                'signals': [
                    {
                        "priority": 1,
                        "action": "BUY",
                        "indicator": "RSI",
                        "value": 45.6,
                        "reason": "Умеренная перепроданность"
                    }
                ]
            },
            'history': {
                'dates': [d.strftime('%Y-%m-%d') for d in dates],
                'prices': [8000 + i*12.5 for i in range(30)]
            }
        }
    }
    return test_data