#!/usr/bin/env sh
set -eu

echo "---- Render boot ----"
echo "PORT=$PORT"
echo "DATABASE_URL=${DATABASE_URL:-<not set>}"

# Fail fast if Render didn't inject PORT
: "${PORT:?PORT is not set}"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn on 0.0.0.0:$PORT ..."
exec gunicorn edulife.wsgi:application \
  --bind "0.0.0.0:$PORT" \
  --workers 2 \
  --threads 2 \
  --timeout 120