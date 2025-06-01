# Этот файл предназначен для Python-кода на стороне клиента (если потребуется).
# Например, с использованием PyScript или Brython.

import asyncio
from pyscript import document, when
import pyodide.http
import json # Для разбора JSON ответа
import time # Для вывода времени в консоль (опционально)
import traceback # Добавим, так как он используется в display_error_in_table

# Импортируем функции из tabl2.py
# Предполагается, что PyScript сможет найти этот файл в той же директории
# Если будут проблемы, возможно, потребуется более явное указание пути или другая конфигурация PyScript
# На данный момент PyScript обычно автоматически загружает соседние .py файлы, если они импортируются.
import tabl2
# import tabl1 # Закомментируем или удалим глобальный импорт

# Попытка импорта из grafik.py для проверки его загрузки и для вызова функции
try:
    from grafik import display_chart_error, set_external_historical_data
except ImportError as e:
    print(f"ФРОНТЕНД (main.py): Не удалось импортировать функции из grafik.py: {e}")
    def display_chart_error(message): pass # Заглушка
    def set_external_historical_data(data): pass # Заглушка

# Конфигурация
API_METALS_URL = '/api/metals' # URL нашего бэкенд API
UPDATE_INTERVAL_SECONDS = 300  # 5 минут в секундах
# API_HISTORICAL_METALS_URL и all_historical_data_cache теперь в tabl2.py

def display_error_in_table(message):
    table_body = document.querySelector("#metals-table tbody")
    if not table_body:
        print(f"ОШИБКА ФРОНТЕНДА: Элемент tbody таблицы 'metals-table' не найден для отображения ошибки: {message}")
        return
    table_body.innerHTML = f'<tr><td colspan="4" style="color: red; text-align: center;">{message}</td></tr>'
    print(f"ФРОНТЕНД: Отображена ошибка в таблице: {message}")

def populate_metal_table(metals_list):
    table_body = document.querySelector("#metals-table tbody")
    if not table_body:
        print("ОШИБКА ФРОНТЕНДА: Элемент tbody таблицы 'metals-table' не найден.")
        return

    table_body.innerHTML = "" # Очищаем предыдущие строки

    if not metals_list:
        display_error_in_table("Нет данных для отображения от API.")
        return

    new_rows_html = ""
    for i, metal in enumerate(metals_list):
        
        name_val = metal.get("name", "N/A")
        price_val = metal.get("price", "N/A")
        unit_val = metal.get("unit", "руб./грамм")
        date_val = metal.get("date", "N/A")
        
        # Формируем HTML для строки
        row_html = f"<tr><td>{name_val}</td><td>{price_val}</td><td>{unit_val}</td><td>{date_val}</td></tr>"
        new_rows_html += row_html
        
    table_body.innerHTML = new_rows_html

async def fetch_and_update_metals_data():
    print(f"ФРОНТЕНД (main.py): Попытка запроса данных с {API_METALS_URL} в {time.strftime('%H:%M:%S')}")
    try:
        response = await pyodide.http.pyfetch(API_METALS_URL)
        
        api_response_text = await response.string()
        # print(f"ФРОНТЕНД: Ответ от API получен: {api_response_text[:200]}...") # Логируем часть ответа
        api_data = json.loads(api_response_text)

        if response.status != 200:
            error_message = f"Ошибка HTTP: {response.status} при запросе к {API_METALS_URL}. Ответ: {api_data.get('error', api_response_text)}"
            print(error_message)
            display_error_in_table(error_message)
            return

        if api_data.get("error"):
            # Используем более информативное сообщение, если ошибка пришла от бэкенда
            error_message = f'Ошибка от API бэкенда: {api_data["error"]}'
            if api_data.get("last_successful_data_update", 0) == 0 and not api_data.get("data"):
                 error_message += " (Данные с ЦБ еще ни разу не были успешно загружены сервером)"
            print(error_message)
            display_error_in_table(error_message)
            # Если есть старые данные, но ошибка, можно их показать, но пока просто ошибка
            # if api_data.get("data"):
            #     populate_metal_table(api_data.get("data")) # Показать старые данные с сообщением об ошибке обновления
            return
        
        metals = api_data.get("data")
        if metals:
            populate_metal_table(metals)
            # last_updated_server_readable = time.ctime(api_data.get("last_successful_data_update", 0)) if api_data.get("last_successful_data_update") else "N/A"
            # print(f"ФРОНТЕНД: Данные успешно загружены. Последнее успешное обновление на сервере: {last_updated_server_readable}")
        else:
            display_error_in_table("API бэкенда вернуло ответ без данных и без явной ошибки.")
            print("ФРОНТЕНД (main.py): API бэкенда вернуло пустые данные без явной ошибки.")

    except Exception as e:
        error_message = f"Критическая ошибка в fetch_and_update_metals_data (main.py): {e}"
        print(error_message)
        display_error_in_table(error_message)
        traceback.print_exc() # Для более детальной отладки в консоли браузера

async def main_loop():
    print(f"ФРОНТЕНД (main.py): Запуск основного цикла.")
    
    # Импортируем tabl1 здесь, прямо перед использованием
    import tabl1
    print(f"ФРОНТЕНД (main.py): tabl1 импортирован внутри main_loop: {type(tabl1)}")

    # Однократная загрузка исторических данных при старте из tabl2.py
    historical_data_loaded_successfully = await tabl2.fetch_historical_data_once()
    await asyncio.sleep(0.1) 
    
    # Передаем загруженные исторические данные в модуль grafik
    if historical_data_loaded_successfully and tabl2.all_historical_data_cache:
        set_external_historical_data(tabl2.all_historical_data_cache)
        print("ФРОНТЕНД (main.py): Исторические данные переданы в grafik.py.")
    else:
        print("ФРОНТЕНД (main.py): Исторический кэш в tabl2 пуст или не был загружен, не передаем в grafik.")

    # Первоначальная загрузка актуальных цен
    print("ФРОНТЕНД (main.py): Первоначальная загрузка актуальных цен из tabl1...")
    await tabl1.fetch_and_update_actual_metals_data()

    # Основной цикл для обновления актуальных цен из tabl1.py
    while True:
        await tabl1.fetch_and_update_actual_metals_data() 
        print(f"ФРОНТЕНД (main.py): Ожидание {tabl1.UPDATE_INTERVAL_SECONDS} секунд до следующего обновления актуальных цен... ({time.strftime('%H:%M:%S')})")
        await asyncio.sleep(tabl1.UPDATE_INTERVAL_SECONDS)

print("ФРОНТЕНД (main.py): PyScript (main.py) загружен. Запуск основного цикла...")
asyncio.ensure_future(main_loop()) 