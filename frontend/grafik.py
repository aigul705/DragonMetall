print("ФРОНТЕНД (grafik.py): Файл grafik.py НАЧАЛ ВЫПОЛНЯТЬСЯ.")
import asyncio
from pyscript import document, when, window, Element
# from pyscript.ffi import to_js # Комментируем или удаляем этот импорт
from pyodide.ffi import to_js # Добавляем импорт из pyodide.ffi
import json
import time
import traceback
from datetime import datetime # Для работы с датами
import js # Явный импорт для работы с JavaScript объектами

# Локальный кэш для данных, полученных из main.py
grafik_local_cache = {}

# Попытка импортировать display_error_in_historical_table из tabl2.py (если он там еще нужен для чего-то, кроме основного кэша)
# и all_historical_data_cache (хотя мы его напрямую использовать не будем, но импорт может быть нужен для PyScript)
try:
    from tabl2 import display_error_in_historical_table, all_historical_data_cache as tabl2_cache_ref # Импортируем для разрешения зависимостей, но использовать будем grafik_local_cache
except ImportError:
    print("ОШИБКА ИМПОРТА (grafik.py): Не удалось импортировать из tabl2.py. Часть функционала может не работать.")
    def display_error_in_historical_table(message):
        print(f"FALLBACK DISPLAY ERROR (grafik.py): {message}")
    tabl2_cache_ref = None # Заглушка

# Глобальная переменная для хранения экземпляра графика, чтобы его можно было обновлять или уничтожать
current_chart = None
# historical_data_is_ready = False # Убираем флаг

# def mark_historical_data_as_ready(): # Убираем функцию
#     global historical_data_is_ready
#     historical_data_is_ready = True
#     print("ФРОНТЕНД (grafik.py): Получен сигнал - исторические данные готовы.")

def set_external_historical_data(data):
    global grafik_local_cache
    grafik_local_cache = data
    print(f"ФРОНТЕНД (grafik.py): Внешние исторические данные установлены. Ключи: {list(grafik_local_cache.keys())}")

def display_chart_error(message):
    error_display = Element("chart-error-message") # Предполагается, что есть такой элемент в HTML
    if error_display:
        error_display.element.innerText = message
        error_display.remove_class("hidden")
    else:
        print(f"ФРОНТЕНД (grafik.py): Элемент для отображения ошибок графика #chart-error-message не найден. Ошибка: {message}")

# Функция для преобразования даты из "ДД.ММ.ГГГГ" в объект Python datetime
def parse_custom_date(date_str):
    if not date_str or date_str == "N/A":
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        print(f"Ошибка парсинга даты (grafik.py): {date_str}")
        return None

# Функция для преобразования даты из "YYYY-MM-DD" (из input) в объект Python datetime
def parse_input_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"Ошибка парсинга даты из поля ввода (grafik.py): {date_str}")
        return None

def create_test_chart():
    print("ФРОНТЕНД (grafik.py): Попытка создания нового тестового графика...")
    global current_chart
    try:
        # 1. Проверка доступности Chart.js
        if not hasattr(js, 'Chart'):
            error_msg = "ФРОНТЕНД (grafik.py): ОБНАРУЖЕНО: js.Chart не существует! Убедитесь, что Chart.js CDN подключен и загружен."
            print(error_msg)
            display_chart_error("Ошибка: Chart.js библиотека не найдена.")
            return
        print(f"ФРОНТЕНД (grafik.py): js.Chart найден. Тип: {type(js.Chart)}")

        # 2. Получение элемента canvas через js.document
        # Используем js.document.getElementById напрямую, так как Element() от PyScript может иметь свои особенности
        canvas_el_js = js.document.getElementById('metalsPriceChart')
        if not canvas_el_js:
            error_msg = "ФРОНТЕНД (grafik.py): ОБНАРУЖЕНО: Элемент canvas с ID 'metalsPriceChart' не найден через js.document.getElementById!"
            print(error_msg)
            display_chart_error("Ошибка: Canvas элемент 'metalsPriceChart' не найден.")
            return
        print(f"ФРОНТЕНД (grafik.py): Canvas элемент 'metalsPriceChart' найден через js.document. Тип элемента: {type(canvas_el_js)}")

        # 3. Получение 2D контекста
        ctx = canvas_el_js.getContext('2d')
        if not ctx:
            error_msg = "ФРОНТЕНД (grafik.py): ОБНАРУЖЕНО: Не удалось получить 2D контекст из canvas элемента!"
            print(error_msg)
            display_chart_error("Ошибка: Не удалось получить 2D контекст для графика.")
            return
        print(f"ФРОНТЕНД (grafik.py): 2D контекст получен. Тип контекста: {type(ctx)}")

        config = {
            "type": "bar", # Используем bar для простоты, как в примере Chart.js
            "data": {
                "labels": ["Красный", "Синий", "Желтый", "Зеленый", "Фиолетовый", "Оранжевый"],
                "datasets": [{
                    "label": "# тестовых голосов",
                    "data": [12, 19, 3, 5, 2, 3],
                    "backgroundColor": [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(255, 159, 64, 0.2)'
                    ],
                    "borderColor": [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    "borderWidth": 1
                }]
            },
            "options": {
                "scales": {"y": {"beginAtZero": True}}, # Упрощенные options
                "responsive": True,
                "maintainAspectRatio": False # Важно для правильного размера в контейнере
            }
        }

        # 4. Преобразование конфигурации в JavaScript объект
        # to_js должен корректно преобразовывать вложенные dict и list
        js_config = to_js(config, dict_converter=js.Object.fromEntries)
        print(f"ФРОНТЕНД (grafik.py): Конфигурация для Chart.js подготовлена. Тип js_config: {type(js_config)}")

        if current_chart:
            try:
                current_chart.destroy()
                print("ФРОНТЕНД (grafik.py): Старый график (если был) уничтожен.")
            except Exception as e_destroy:
                print(f"ФРОНТЕНД (grafik.py): Ошибка при уничтожении старого графика: {e_destroy}")
        
        # 5. Создание графика
        print("ФРОНТЕНД (grafik.py): Вызов js.Chart.new(ctx, js_config)...")
        current_chart = js.Chart.new(ctx, js_config) # Используем js.Chart.new
        print("ФРОНТЕНД (grafik.py): Вызов js.Chart.new ЗАВЕРШЕН.")

        if current_chart:
            print(f"ФРОНТЕНД (grafik.py): Экземпляр графика СОЗДАН. Тип current_chart: {type(current_chart)}. График должен отобразиться.")
        else:
            print("ФРОНТЕНД (grafik.py): ОБНАРУЖЕНО: js.Chart.new вернул None или Falsy значение! График не создан.")
            display_chart_error("Ошибка: Chart.js не смог создать экземпляр графика (js.Chart.new вернул null/undefined).")

    except Exception as e:
        error_msg_critical = f"ФРОНТЕНД (grafik.py): КРИТИЧЕСКАЯ ОШИБКА Python при создании тестового графика: {e}"
        print(error_msg_critical)
        import traceback
        print(traceback.format_exc())
        display_chart_error(f"Критическая ошибка Python: {e}")

@when("click", "#update-chart-button")
def handle_update_chart_button_click_TEST(event=None):
    print("ФРОНТЕНД (grafik.py): Нажата кнопка 'Показать график' (ID: #update-chart-button) - ЗАПУСК ТЕСТА МИНИМАЛЬНОГО ГРАФИКА")
    create_test_chart()

# async def delayed_chart_creation():
# await asyncio.sleep(0.1) # Маленькая пауза
# create_test_chart()

# Важно: реальная функция handle_update_chart_button_click для работы с данными пока закомментирована
# или должна быть переименована, чтобы не конфликтовать с тестовой.
# Убедитесь, что именно handle_update_chart_button_click_TEST привязана к кнопке, если это основная отладочная функция.

# # Ваш предыдущий код для работы с реальными данными пока закомментирован
# metal_select = document.querySelector("#chart-metal-select")
# date_start_input = document.querySelector("#chart-date-start")
# date_end_input = document.querySelector("#chart-date-end")

# selected_metal = metal_select.value
# date_start_str = date_start_input.value
# date_end_str = date_end_input.value
# print(f"ФРОНТЕНД (grafik.py): Параметры для графика: Металл={selected_metal}, Старт={date_start_str}, Конец={date_end_str}")
# 
# grafik_local_cache = get_historical_data_cache_from_main() # или как вы там его получаете
# print(f"DEBUG (grafik.py): Проверка grafik_local_cache: {'Ключи: ' + str(list(grafik_local_cache.keys())) if grafik_local_cache else 'Кэш пуст или None'}")

# if not grafik_local_cache:
#     display_chart_error("Локальный кэш исторических данных в grafik.py пуст. Невозможно построить график.")
#     return

# metal_historical_data = grafik_local_cache.get(selected_metal)
# print(f"DEBUG (grafik.py): Данные для металла '{selected_metal}': {str(metal_historical_data[:2]) + '...' if metal_historical_data and len(metal_historical_data) > 2 else str(metal_historical_data) if metal_historical_data else 'Нет данных'}")

# if not metal_historical_data:
#     display_chart_error(f"Нет исторических данных для металла '{selected_metal}'.")
#     return

# # Фильтрация данных по дате
# date_start_obj = parse_input_date(date_start_str)
# date_end_obj = parse_input_date(date_end_str)
# print(f"DEBUG (grafik.py): Распарсенные даты: Старт={date_start_obj}, Конец={date_end_obj}")

# filtered_entries = []
# for entry in metal_historical_data:
#     entry_date_str = entry.get("date")
#     entry_price_str = entry.get("price")
#     entry_date_obj = parse_custom_date(entry_date_str)

#     if entry_date_obj and entry_price_str != "N/A":
#         valid_entry = True
#         if date_start_obj and entry_date_obj < date_start_obj:
#             valid_entry = False
#         if date_end_obj and entry_date_obj > date_end_obj:
#             valid_entry = False
#         
#         if valid_entry:
#             try:
#                 price = float(entry_price_str.replace(',', '.')) 
#                 filtered_entries.append({"date": entry_date_obj, "price": price, "date_str": entry_date_str})
#             except ValueError:
#                 print(f"Пропуск записи для графика: не удалось преобразовать цену '{entry_price_str}' в число для даты {entry_date_str}")
# 
# print(f"DEBUG (grafik.py): Количество отфильтрованных записей: {len(filtered_entries)}")
# if filtered_entries:
#     print(f"DEBUG (grafik.py): Первая отфильтрованная запись: {filtered_entries[0]}")

# if not filtered_entries:
#     display_chart_error(f"Нет данных для графика для металла '{selected_metal}' в указанном диапазоне дат.")
#     return

# filtered_entries.sort(key=lambda x: x["date"])

# labels = [entry["date_str"] for entry in filtered_entries]
# data_points = [entry["price"] for entry in filtered_entries]
# print(f"DEBUG (grafik.py): Метки для графика (первые 5): {labels[:5]}")
# print(f"DEBUG (grafik.py): Точки данных для графика (первые 5): {data_points[:5]}")

# chart_data = {
#     'type': 'line',
#     'data': {
#         'labels': to_js(labels),
#         'datasets': [{
#             'label': f'Цена на {selected_metal} (руб./грамм)',
#             'data': to_js(data_points),
#             'fill': False,
#             'borderColor': 'rgb(75, 192, 192)',
#             'tension': 0.1
#         }]
#     },
#     'options': {
#         'responsive': True,
#         'maintainAspectRatio': True, 
#         'scales': {
#             'y': {
#                 'beginAtZero': False
#             }
#         }
#     }
# }

# ctx = document.getElementById('metalsPriceChart').getContext('2d')
# 
# if current_chart:
#     current_chart.destroy()

# current_chart = window.Chart.new(ctx, to_js(chart_data))
# print(f"ФРОНТЕНД (grafik.py): График для '{selected_metal}' обновлен/построен.")

print("ФРОНТЕНД (grafik.py): Модуль grafik.py загружен.") 