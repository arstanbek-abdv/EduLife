#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import os, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edulife.settings')
import django
django.setup()
from django.db import connection
for i in range(60):
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

echo "Creating superuser if missing..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print('Superuser created:', username)
    else:
        print('Superuser already exists:', username)
else:
    print('Superuser env vars not set; skipping')
" || true

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

: "${PORT:?PORT is not set}"

echo "Starting gunicorn on port $PORT..."
exec gunicorn edulife.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 2 \
  --timeout 120