#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
sleep 5

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Use gunicorn in production (Render sets PORT); fall back to runserver locally
if [ -n "$PORT" ]; then
    echo "Starting gunicorn on port $PORT..."
    exec gunicorn heritage_backend.wsgi:application \
        --bind "0.0.0.0:$PORT" \
        --workers 2 \
        --timeout 120 \
        --access-logfile -
else
    echo "Starting development server on port 8000..."
    exec python manage.py runserver 0.0.0.0:8000
fi
