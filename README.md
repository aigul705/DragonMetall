Для запуска открываем 2 командных строки и в обоих переходим в папку данного проекта

#в первой командной строке(попорядку)
1) py -3.11 --version
2) rmdir /s /q .venv
3) .\.venv\Scripts\activate    (между первыми двумя точками наклонная черта влево)
4) pip install --default-timeout=100 -r requirements.txt
5) cd AI_module
6) uvicorn metal_forecast_api:app --port 8001

#во второй командной строке
1) cd backend
2) python -m venv .venv
3) .venv\Scripts\activate
4) pip install --default-timeout=100 lxml
5) python main.py

в поисковой строке переходим по localhost:8000 и смотрим