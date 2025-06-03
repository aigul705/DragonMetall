from core.data.fetcher import MetalDataFetcher
from core.analysis.trends import TrendAnalyzer
from datetime import datetime
from core.data.test_data import get_test_data 


class RecommendationService:
    def __init__(self):
        self.fetcher = MetalDataFetcher()
        self.analyzer = TrendAnalyzer()
        
    def get_recommendations(self):
        """Получает и возвращает рекомендации по всем металлам"""
        try:
            # Получаем данные по всем металлам
            raw_df = self.fetcher.fetch(days=30)
            if raw_df.empty:
                print("No data fetched from source")
                return {
                    "status": "error",
                    "message": "Не удалось получить данные",
                    "timestamp": datetime.now().isoformat(),
                    "data": {}
                }

            results = {}
            metals_to_process = ['Au', 'Ag', 'Pt', 'Pd']  # Все металлы, которые нужно обработать
            
            for metal in metals_to_process:
                try:
                    # Фильтруем данные по текущему металлу
                    metal_data = raw_df[raw_df['metal'] == metal]
                    if metal_data.empty:
                        print(f"No data for {metal}, generating test data")
                        # Генерируем тестовые данные, если нет реальных
                        metal_data = self._generate_test_data(metal)
                    
                    # Анализируем данные
                    metal_analysis = self.analyzer.analyze(metal_data, metal)
                    
                    if 'error' in metal_analysis:
                        print(f"Analysis error for {metal}: {metal_analysis['error']}")
                        continue
                        
                    # Добавляем исторические данные
                    metal_analysis['history'] = {
                        'dates': metal_data['date'].dt.strftime('%Y-%m-%d').tolist(),
                        'prices': metal_data['price'].astype(float).tolist()
                    }
                    
                    results[metal] = metal_analysis
                    
                except Exception as e:
                    print(f"Error processing {metal}: {str(e)}")
                    continue

            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": results
            }
            
        except Exception as e:
            print(f"Recommendation service error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
                "data": {}
            }

    def _generate_test_data(self, metal):
        """Генерирует тестовые данные для металла"""
        from datetime import datetime, timedelta
        import pandas as pd
        import numpy as np
        
        dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
        base_prices = {
            'Au': 8000,
            'Ag': 80,
            'Pt': 2500,
            'Pd': 2000
        }
        
        prices = np.linspace(
            base_prices.get(metal, 1000) * 0.9,
            base_prices.get(metal, 1000) * 1.1,
            30
        )
        
        return pd.DataFrame({
            'date': dates,
            'metal': metal,
            'price': prices
        })