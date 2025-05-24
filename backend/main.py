import http.server
import socketserver
import os
import json
import time
from threading import Lock # Добавляем Lock для безопасного обновления данных
import re # <--- Добавляем импорт re

# Попытка импортировать библиотеки для парсинга
try:
    import requests
    from bs4 import BeautifulSoup
    IMPORTS_SUCCESSFUL = True
except ImportError:
    IMPORTS_SUCCESSFUL = False
    print("ПРЕДУПРЕЖДЕНИЕ: Библиотеки 'requests' и 'beautifulsoup4' не найдены. API металлов не будет обновлять цены с ЦБ.")
    print("Пожалуйста, установите их: pip install requests beautifulsoup4")

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(__file__), '../frontend') # Указываем на папку frontend
METALS_URL = 'https://mfd.ru/centrobank/preciousmetals/'

# Базовая структура данных о металлах (названия и единицы остаются статичными)
# Цены и даты будут обновляться
metals_cache = [
    {"name": "Золото", "price": "N/A", "unit": "руб./грамм", "date": "N/A"},
    {"name": "Серебро", "price": "N/A", "unit": "руб./грамм", "date": "N/A"},
    {"name": "Платина", "price": "N/A", "unit": "руб./грамм", "date": "N/A"},
    {"name": "Палладий", "price": "N/A", "unit": "руб./грамм", "date": "N/A"}
]
# Кэш для исторических данных
# Структура: {"металл": [{"date": "ДД.ММ.ГГГГ", "price": "ЦЕНА"}, ...], ...}
historical_metals_data_cache = {}
last_successful_update_time = 0
metals_data_lock = Lock() # Мьютекс для защиты metals_cache, historical_metals_data_cache и last_successful_update_time
# Глобальная переменная для хранения ошибки парсинга, если она возникла
parsing_error_message = None

def fetch_and_update_metal_prices():
    global metals_cache, historical_metals_data_cache, last_successful_update_time, parsing_error_message
    if not IMPORTS_SUCCESSFUL:
        parsing_error_message = "Сервер не может обновить цены: отсутствуют библиотеки requests/beautifulsoup4."
        print(parsing_error_message)
        # В этом случае цены и даты останутся "N/A" или последними успешными
        return

    print(f"Попытка обновления цен на металлы с {METALS_URL}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(METALS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ИЗМЕНЕННЫЙ СЕЛЕКТОР ТАБЛИЦЫ
        table = soup.find('table', class_='mfd-table') 
        if not table:
            parsing_error_message = "Не удалось найти таблицу с классом 'mfd-table' на mfd.ru."
            print(parsing_error_message)
            return

        # Ищем tbody внутри найденной таблицы
        tbody = table.find('tbody')
        if not tbody:
            parsing_error_message = "Не удалось найти tbody в таблице на mfd.ru."
            print(parsing_error_message)
            return

        data_rows = tbody.find_all('tr') # Получаем все строки из tbody
        if not data_rows: # Проверяем, есть ли вообще строки с данными
            parsing_error_message = "В tbody таблицы не найдено строк (tr) с данными."
            print(parsing_error_message)
            return
            
        # Обработка актуальных цен (первая строка)
        latest_data_row_cells = data_rows[0].find_all('td')
        if not latest_data_row_cells or len(latest_data_row_cells) < 5:
            parsing_error_message = "Не удалось извлечь ячейки из первой строки данных tbody или их количество неверно."
            print(parsing_error_message)
            return

        # Регулярное выражение для извлечения цены (число с точкой или запятой как разделителем)
        # Оно ищет числа вида 1234.56 или 1 234.56 или 1 234,56 и т.п. в начале строки
        # Также учитываем, что разделителем тысяч может быть пробел, а десятичным - точка или запятая
        price_pattern = re.compile(r"^(\d+(?:[.,]\d{1,4})?)")
        # Регулярное выражение для извлечения даты в формате ДД.ММ.ГГГГ
        date_pattern = re.compile(r"^(\d{2}\.\d{2}\.\d{4})")

        def extract_value_with_regex(text, pattern, default_value="N/A"):
            match = pattern.match(text)
            if match:
                # Для цен удаляем пробелы и заменяем запятую на точку для унификации
                value = match.group(1).replace(' ', '').replace(',', '.')
                return value
            return default_value

        # Извлекаем текст даты из первой ячейки
        date_text_content = latest_data_row_cells[0].text.strip()
        current_date = extract_value_with_regex(date_text_content, date_pattern)
        
        if current_date == "N/A":
            print(f"DEBUG_PARSER: Не удалось извлечь дату из текста: '{date_text_content}'")

        prices_from_site = {}
        # Индексы ячеек: 0-дата, 1-золото, 2-серебро, 3-платина, 4-палладий
        metal_names_in_order = ["Золото", "Серебро", "Платина", "Палладий"]
        
        for i, metal_name in enumerate(metal_names_in_order):
            cell_index = i + 1 # Цены начинаются со второй ячейки (индекс 1)
            if cell_index < len(latest_data_row_cells):
                price_text_content = latest_data_row_cells[cell_index].text.strip()
                extracted_price = extract_value_with_regex(price_text_content, price_pattern)
                prices_from_site[metal_name] = extracted_price
                if extracted_price == "N/A":
                    print(f"DEBUG_PARSER: Не удалось извлечь цену для '{metal_name}' из текста: '{price_text_content[:100]}...'")
            else:
                prices_from_site[metal_name] = "N/A"
                print(f"DEBUG_PARSER: Ячейка для '{metal_name}' (индекс {cell_index}) отсутствует.")

        # Обработка исторических данных (начиная со второй строки)
        temp_historical_data = {name: [] for name in metal_names_in_order}
        if len(data_rows) > 1:
            for row_idx, data_row in enumerate(data_rows[1:], start=1): # Пропускаем первую строку (актуальные цены)
                historical_row_cells = data_row.find_all('td')
                if not historical_row_cells or len(historical_row_cells) < 5:
                    print(f"DEBUG_PARSER: Пропуск исторической строки {row_idx+1}: неверное количество ячеек.")
                    continue

                date_text_content_hist = historical_row_cells[0].text.strip()
                historical_date = extract_value_with_regex(date_text_content_hist, date_pattern)

                if historical_date == "N/A":
                    print(f"DEBUG_PARSER: Пропуск исторической строки {row_idx+1}: не удалось извлечь дату из '{date_text_content_hist}'.")
                    continue
                
                for i, metal_name in enumerate(metal_names_in_order):
                    cell_idx_hist = i + 1
                    if cell_idx_hist < len(historical_row_cells):
                        price_text_hist = historical_row_cells[cell_idx_hist].text.strip()
                        price_hist = extract_value_with_regex(price_text_hist, price_pattern)
                        if price_hist != "N/A":
                            temp_historical_data[metal_name].append({"date": historical_date, "price": price_hist})
                        else:
                            print(f"DEBUG_PARSER: Пропуск цены для '{metal_name}' в исторической строке {row_idx+1} (дата {historical_date}): не удалось извлечь цену из '{price_text_hist[:50]}...'.")
                    else:
                        print(f"DEBUG_PARSER: Отсутствует ячейка для '{metal_name}' в исторической строке {row_idx+1} (дата {historical_date}).")
        
        with metals_data_lock:
            # Обновляем кэш актуальных цен
            for metal_entry in metals_cache:
                metal_name = metal_entry["name"]
                if metal_name in prices_from_site:
                    metal_entry["price"] = prices_from_site[metal_name]
                    metal_entry["date"] = current_date
            # Обновляем кэш исторических данных
            historical_metals_data_cache = temp_historical_data
            
            last_successful_update_time = time.time()
            parsing_error_message = None
        print(f"Цены на металлы успешно обновлены (обработаны): {time.ctime(last_successful_update_time)}")

    except requests.exceptions.RequestException as e:
        parsing_error_message = f"Ошибка сети при запросе к mfd.ru: {e}"
        print(parsing_error_message)
    except Exception as e:
        parsing_error_message = f"Произошла ошибка при парсинге данных mfd.ru: {e}"
        print(parsing_error_message)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == '/api/hello':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # Используем json.dumps для корректного формирования JSON
            self.wfile.write(json.dumps({"message": "Hello from backend!"}).encode('utf-8'))
            return
        elif self.path == '/api/metals': # <--- НОВЫЙ ОБРАБОТЧИК
            current_time = time.time()
            # Обновляем, если прошло больше 5 минут с последнего успешного обновления
            # или если это первый запуск (last_successful_update_time == 0)
            # или если была ошибка при последней попытке парсинга (чтобы попытаться снова)
            with metals_data_lock: # Блокируем для чтения last_successful_update_time и parsing_error_message
                needs_update = (current_time - last_successful_update_time > 300) or \
                               (last_successful_update_time == 0) or \
                               (parsing_error_message is not None) 

            if needs_update:
                fetch_and_update_metal_prices() # Попытка обновить данные

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with metals_data_lock: # Блокируем для безопасного чтения metals_cache и parsing_error_message
                # Отдаем текущее состояние кеша, даже если обновление не удалось
                # Фронтенд сможет показать последнюю успешную цену или "N/A"
                # А также ошибку, если она есть
                response_data = {
                    "data": metals_cache, # Отдаем текущее состояние кеша
                    "error": parsing_error_message, # Передаем сообщение об ошибке парсинга, если есть
                    "last_updated_attempt": time.time(), # Время текущего запроса к API
                    "last_successful_data_update": last_successful_update_time
                }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
        elif self.path == '/api/historical_metals': # <--- НОВЫЙ ОБРАБОТЧИК ДЛЯ ИСТОРИЧЕСКИХ ДАННЫХ
            # Данные должны быть уже обновлены через /api/metals или при старте, 
            # поэтому здесь просто отдаем кеш. При необходимости можно добавить логику обновления.
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with metals_data_lock: # Блокируем для безопасного чтения
                response_data_hist = {
                    "data": historical_metals_data_cache,
                    "error": parsing_error_message, 
                    "last_successful_data_update": last_successful_update_time
                }
            self.wfile.write(json.dumps(response_data_hist).encode('utf-8'))
            return
            
        super().do_GET()

# Запускаем первичную попытку обновления цен при старте сервера
# Это не будет блокировать запуск сервера надолго, если сайт ЦБ недоступен,
# т.к. fetch_and_update_metal_prices() обрабатывает таймауты и ошибки.
print("Первоначальная попытка обновления цен на металлы...")
fetch_and_update_metal_prices() 
# В реальном приложении можно было бы запустить это в отдельном потоке, 
# чтобы не задерживать старт сервера, но для SimpleHTTPRequestHandler это усложнение.

# Основной цикл сервера
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Сервер запущен на порту {PORT}")
    print(f"Раздача файлов из: {WEB_DIR}")
    print(f"Доступны эндпоинты: /api/hello, /api/metals (цены и даты обновляются с ЦБ), /api/historical_metals")
    if not IMPORTS_SUCCESSFUL:
        print(">>> ВНИМАНИЕ: Библиотеки requests/beautifulsoup4 не найдены. Цены на металлы не будут обновляться с сайта ЦБ и могут отображаться как N/A.")
    httpd.serve_forever() 