import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

class PricePredictor:
    def __init__(self, n_estimators=100):
        self.model = RandomForestRegressor(n_estimators=n_estimators)
        
    def train(self, X, y):
        """Обучение модели"""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        self.model.fit(X_train, y_train)
        
        # Оценка качества
        preds = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        print(f"MAE модели: {mae:.2f}")
        
    def predict(self, X):
        """Прогнозирование цены"""
        return self.model.predict(X)
    
    def prepare_data(self, df, lookback=14):
        """Подготовка данных для временных рядов"""
        X, y = [], []
        prices = df['price'].values
        
        for i in range(lookback, len(prices)):
            X.append(prices[i-lookback:i])
            y.append(prices[i])
            
        return np.array(X), np.array(y)