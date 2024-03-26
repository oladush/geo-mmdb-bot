**Подготовка конфиг файла**  
Для запуска и работы необходимо прописать в config.ini:  
`secret = SOME_ANY_SECRET` (любая случайная строка)  
`token = TELEGRAM_BOT_TOKEN` (токен телеграм бота)  

**Установка зависимостей и запуск:**  
`python3 -m pip install -r requirements.txt`  
`python3 bot.py`

**Запуск через Докер контейнер:**   
`docker build -t geo-mmdb-bot .`  
`docker run --name geo_mmdb_bot geo-mmdb-bot`