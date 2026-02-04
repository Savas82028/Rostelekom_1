#!/bin/bash
# Запуск эмулятора роботов в фоне + gunicorn
# Render: PORT задаётся платформой

PORT=${PORT:-10000}
export API_URL="${API_URL:-http://127.0.0.1:${PORT}}"

# Эмулятор роботов в фоне
nohup python robot_emulator.py >> /tmp/robot_emulator.log 2>&1 &

# Gunicorn (основной процесс)
exec gunicorn -b 0.0.0.0:${PORT} app:app
