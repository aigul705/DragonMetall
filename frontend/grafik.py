import asyncio
from pyscript import document
from pyodide.ffi import to_js, create_proxy
import json
import time
import traceback
from datetime import datetime
import js

# Локальный кэш для данных, полученных из main.py
grafik_local_cache = {}


try:
    from tabl2 import display_error_in_historical_table, all_historical_data_cache as tabl2_cache_ref # Импортируем для разрешения зависимостей, но использовать будем grafik_local_cache
except ImportError:
    tabl2_cache_ref = None # Заглушка

# Глобальная переменная для хранения экземпляра графика, чтобы его можно было обновлять или уничтожать
current_chart = None
def set_external_historical_data(data):
    global grafik_local_cache
    grafik_local_cache = data
    

def display_chart_error(message):
    # Попробуем найти существующий элемент или создать его, если это необходимо
    error_display_container = document.querySelector("#chart-error-container") # Используем контейнер
    if not error_display_container:
        return
    
    error_display_container.innerHTML = f'<p style="color: red; text-align: center;">{message}</p>'
   

# Функция для преобразования даты из "ДД.ММ.ГГГГ" в объект Python datetime
def parse_custom_date(date_str):
    if not date_str or date_str == "N/A":
        return None
    return datetime.strptime(date_str, "%d.%m.%Y")
    

# Функция для преобразования даты из "YYYY-MM-DD" (из input) в объект Python datetime
def parse_input_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None



async def handle_update_chart_button_click(event=None):
    global current_chart, grafik_local_cache

    metal_select_element = document.querySelector("#chart-metal-select")
    date_start_input = document.querySelector("#chart-date-start")
    date_end_input = document.querySelector("#chart-date-end")

    if not (metal_select_element and date_start_input and date_end_input):
        display_chart_error("Не удалось найти элементы управления фильтрами графика.")
        return

    selected_metal = metal_select_element.value
    date_start_str = date_start_input.value
    date_end_str = date_end_input.value
    


    if not grafik_local_cache:
        display_chart_error("Исторические данные для графика еще не загружены ")
        return

    metal_historical_data = grafik_local_cache.get(selected_metal)
    
    if not metal_historical_data:
        display_chart_error(f"Нет исторических данных для металла")
        return

    date_start_obj = parse_input_date(date_start_str)
    date_end_obj = parse_input_date(date_end_str)

    filtered_entries = []
    for entry in metal_historical_data:
        entry_date_str = entry.get("date")
        entry_price_str = entry.get("price")
        entry_date_obj = parse_custom_date(entry_date_str)

        if entry_date_obj and entry_price_str is not None and entry_price_str != "N/A":
            valid_entry = True
            if date_start_obj and entry_date_obj < date_start_obj:
                valid_entry = False
            if date_end_obj and entry_date_obj > date_end_obj:
                valid_entry = False
            
            if valid_entry:
                
                    # Убедимся, что цена - это строка перед заменой, затем float
                price_str_cleaned = str(entry_price_str).replace(',', '.')
                price = float(price_str_cleaned)
                filtered_entries.append({"date": entry_date_obj, "price": price, "date_str": entry_date_str})
                
    
    if not filtered_entries:
        display_chart_error(f"Нет данных для графика для металла")
        
        # Очистим график, если он был, и данных нет
        if current_chart:
            
            current_chart.destroy()
            current_chart = None

        canvas_el_js = js.document.getElementById('metalsPriceChart')
        if canvas_el_js:
             ctx = canvas_el_js.getContext('2d')
             ctx.clearRect(0, 0, canvas_el_js.width, canvas_el_js.height)
        return

    filtered_entries.sort(key=lambda x: x["date"])

    labels = [entry["date_str"] for entry in filtered_entries]
    data_points = [entry["price"] for entry in filtered_entries]

    chart_data_config = {
        'type': 'line',
        'data': {
            'labels': to_js(labels), # Преобразуем Python list в JS Array
            'datasets': [{
                'label': f'Цена на {selected_metal} (руб./грамм)',
                'data': to_js(data_points), # Преобразуем Python list в JS Array
                'fill': False,
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'scales': {
                'x': { # Настройки для оси X (даты)
                    'title': {
                        'display': True,
                        'text': 'Дата'
                    }
                },
                'y': { # Настройки для оси Y (цены)
                    'beginAtZero': False, 
                    'title': {
                        'display': True,
                        'text': 'Цена (руб./грамм)'
                    }
                }
            },
            'plugins': {
                'legend': {
                    'position': 'top',
                },
                'title': {
                    'display': True,
                    'text': f'Динамика цен на {selected_metal}'
                }
            }
        }
    }

    try:
        canvas_el_js = js.document.getElementById('metalsPriceChart')
        if not canvas_el_js:
            display_chart_error("Элемент не найден для создания графика.")
            return

        ctx = canvas_el_js.getContext('2d')
        if not ctx:
            display_chart_error("Не удалось получить график")
            return

        if current_chart:
            try:
                current_chart.destroy()
                print("Старый график уничтожен перед созданием нового.")
            except Exception as e_destroy:
                print(f"Ошибка при уничтожении старого графика")
        
        # Используем dict_converter=js.Object.fromEntries для лучшей совместимости с Chart.js 4.x
        js_chart_data_config = to_js(chart_data_config, dict_converter=js.Object.fromEntries)
        
        current_chart = js.Chart.new(ctx, js_chart_data_config)
      
        # Очистим сообщение об ошибке, если график успешно построен
        error_display_container = document.querySelector("#chart-error-container")
        if error_display_container:
            error_display_container.innerHTML = ""


    except Exception as e:
        error_msg_critical = f" ОШИБКА Python при создании/обновлении графика: {e}"
        print(error_msg_critical)
        traceback.print_exc()
        display_chart_error(f"ошибка Python при построении графика: {e}")

def bind_chart_event_handlers():
    try:
        button = document.querySelector("#update-chart-button")
        if button:
            def proxy_handler(_):
                asyncio.ensure_future(handle_update_chart_button_click())
            
            handler = create_proxy(proxy_handler)
            button.addEventListener("click", handler)
    except Exception as e:
        print(f"Ошибка при привязке обработчика для графика: {e}")


