#!/bin/sh
set -e
# Ждём БД и применяем миграции перед стартом приложения
echo "Waiting for database..."
python -c "
import os, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edulife.settings')
import django
django.setup()
from django.db import connection
for i in range(30):
    try:
        connection.ensure_connection()
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit('Database not ready')
"
echo "Running migrations..."
python manage.py migrate --noinput
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 2 edulife.wsgi:application
