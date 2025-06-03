from flask import Flask, jsonify, render_template
from datetime import datetime
from core.recommendation_service import RecommendationService
import os
import json

def create_app():
    # Настройка путей
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_path = os.path.join(base_dir, 'templates')
    static_path = os.path.join(base_dir, 'static')

    app = Flask(__name__,
                template_folder=templates_path,
                static_folder=static_path)

    # Логирование путей для отладки
    print(f"Templates path: {app.template_folder}")
    print(f"Static path: {app.static_folder}")

    @app.route('/')
    def index():
        try:
            return render_template('index.html')
        except Exception as e:
            return f"Ошибка загрузки страницы: {str(e)}", 500

    @app.route('/api/recommendations')
    def get_recommendations():
        """API для получения рекомендаций"""
        def process_metal_data(metal_data):
            """Обрабатывает данные по одному металлу"""
            tech_analysis = metal_data.get('technical_analysis', {})
            signals = tech_analysis.get('signals', [])
            
            main_signal = max(signals, key=lambda x: x.get('priority', 0)) if signals else {
                'action': 'HOLD',
                'reason': 'Недостаточно данных',
                'confidence': 0.5
            }
            
            return {
                'current_price': float(metal_data.get('current_price', 0)),
                'general_recommendation': {
                    'action': main_signal.get('action', 'HOLD'),
                    'confidence': float(main_signal.get('confidence', 0.5)),
                    'description': main_signal.get('reason', '')
                },
                'history': metal_data.get('history', {
                    'dates': [],
                    'prices': []
                }),
                'indicators': tech_analysis.get('indicators', {})
            }

        def create_placeholder_data(metal):
            """Создает заглушку для отсутствующих данных"""
            base_prices = {
                'Au': 8000,
                'Ag': 80,
                'Pt': 2500,
                'Pd': 2000
            }
            
            return {
                'current_price': base_prices.get(metal, 0),
                'general_recommendation': {
                    'action': 'HOLD',
                    'confidence': 0.5,
                    'description': 'Данные временно недоступны'
                },
                'history': {
                    'dates': [],
                    'prices': []
                },
                'indicators': {}
            }

        try:
            service = RecommendationService()
            result = service.get_recommendations()
            
            # Логирование для отладки
            print("Service response:", json.dumps(result, indent=2, ensure_ascii=False))

            # Если сервис вернул ошибку
            if result.get('status') != 'success':
                return jsonify({
                    "status": "error",
                    "message": result.get('message', 'Service error'),
                    "timestamp": datetime.now().isoformat(),
                    "data": {}
                }), 500

            # Обработка данных для фронтенда
            processed_data = {}
            required_metals = ['Au', 'Ag', 'Pt', 'Pd']  # Все необходимые металлы
            
            for metal in required_metals:
                if metal not in result.get('data', {}):
                    print(f"Warning: No data for {metal}, generating placeholder")
                    processed_data[metal] = create_placeholder_data(metal)
                    continue
                    
                metal_data = result['data'][metal]
                try:
                    processed_data[metal] = process_metal_data(metal_data)
                except Exception as e:
                    print(f"Error processing {metal}: {str(e)}")
                    processed_data[metal] = create_placeholder_data(metal)

            return jsonify({
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": processed_data
            })

        except Exception as e:
            print(f"API error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
                "data": {}
            }), 500
    

    @app.route('/api/docs')
    def docs():
        """Документация API"""
        return render_template('docs.html')

    @app.route('/test')
    def test():
        return jsonify({
            "status": "OK",
            "app": "metal_analyzer",
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        })

    return app