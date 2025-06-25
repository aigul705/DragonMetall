Для запуска открываем 2 командных строки и в обоих переходим в папку данного проекта

#в первой командной строке(попорядку)
py -3.11 --version
rmdir /s /q .venv
.\.venv\Scripts\activate
pip install --default-timeout=100 -r requirements.txt
cd AI_module
uvicorn metal_forecast_api:app --port 8001

#во второй командной строке
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install --default-timeout=100 lxml
python main.py

в поисковой строке переходим по localhost:8000 и смотрим