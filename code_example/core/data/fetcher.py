import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import Optional

class MetalDataFetcher:
    def __init__(self):
        self.base_url = "https://www.cbr.ru/scripts/xml_metall.asp"
        self.timeout = 10
        self.metal_codes = {
            'Au': '1',  # Золото
            'Ag': '2',  # Серебро
            'Pt': '3',  # Платина
            'Pd': '4'   # Палладий
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch(self, days: int = 30) -> pd.DataFrame:
        try:

            end_date = datetime.now()
            start_date = end_date - timedelta(days=min(days, 90)) 
            
            params = {
                'date_req1': start_date.strftime('%d/%m/%Y'),
                'date_req2': end_date.strftime('%d/%m/%Y')
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()  # Проверка HTTP ошибок

            return self._parse_response(response.content)
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети: {str(e)}")
        except Exception as e:
            print(f"Неожиданная ошибка: {str(e)}")
            
        return pd.DataFrame(columns=['date', 'metal', 'price'])

    def _parse_response(self, xml_content: bytes) -> pd.DataFrame:
        """Парсинг XML данных в DataFrame"""
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            records = []
            

            for record in soup.find_all('Record'):

                if not all([record.get('Date'), record.get('Code'), record.find('Buy')]):
                    continue
                    
                try:

                    date = datetime.strptime(record['Date'], '%d.%m.%Y')
                    metal = self._code_to_metal(record['Code'])
                    price = float(record.find('Buy').text.replace(',', '.'))
                    
                    records.append({
                        'date': date,
                        'metal': metal,
                        'price': price
                    })
                except (ValueError, KeyError) as e:
                    print(f"Ошибка парсинга записи: {str(e)}")
                    continue
                    
            # Создание DataFrame
            if records:
                df = pd.DataFrame(records)
                return df.sort_values('date').reset_index(drop=True)
                
        except Exception as e:
            print(f"Ошибка парсинга XML: {str(e)}")
            
        return pd.DataFrame(columns=['date', 'metal', 'price'])

    def _code_to_metal(self, code: str) -> Optional[str]:

        for metal, metal_code in self.metal_codes.items():
            if code == metal_code:
                return metal
        return None