import asyncio
from pyscript import document
import pyodide.http
import json
import time
import traceback

# Конфигурация для таблицы актуальных цен
API_METALS_URL = '/api/metals'
UPDATE_INTERVAL_SECONDS = 300  # 5 минут в секундах

def display_error_in_table(message):
    table_body = document.querySelector("#metals-table tbody")
    if not table_body:
        print(f"ОШИБКА Элемент tbody таблицы 'metals-table' не найден ")
        return
    table_body.innerHTML = f'<tr><td colspan="4" style="color: red; text-align: center;">{message}</td></tr>'
    print(f"ошибка в таблице актуальных цен")

def populate_metal_table(metals_list):
    table_body = document.querySelector("#metals-table tbody")
    if not table_body:
        print("Элемент tbody таблицы 'metals-table' не найден.")
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
        
        row_html = f"<tr><td>{name_val}</td><td>{price_val}</td><td>{unit_val}</td><td>{date_val}</td></tr>"
        new_rows_html += row_html
        
    table_body.innerHTML = new_rows_html

async def fetch_and_update_actual_metals_data(): # Переименована для ясности
    
    try:
        response = await pyodide.http.pyfetch(API_METALS_URL)
        api_response_text = await response.string()
        api_data = json.loads(api_response_text)

        if response.status != 200:
            error_message = f"Ошибка HTTP: {response.status} при запросе к {API_METALS_URL}. Ответ: {api_data.get('error', api_response_text)}"
            print(error_message)
            display_error_in_table(error_message)
            return

        if api_data.get("error"):
            error_message = f'Ошибка от API бэкенда'
            if api_data.get("last_successful_data_update", 0) == 0 and not api_data.get("data"):
                 error_message += " (Данные с ЦБ не были успешно загружены )"
            print(error_message)
            display_error_in_table(error_message)
            return
        
        metals = api_data.get("data")
        
    except Exception as e:
        error_message = f" ошибка в fetch_and_update_actual_metals_data : {e}"
        print(error_message)
        display_error_in_table(error_message)
        traceback.print_exc()

print(" Модуль tabl1.py загружен.") 