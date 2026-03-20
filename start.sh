#!/bin/bash
set -e
python manage.py migrate
python manage.py seed_products || true
python manage.py collectstatic --noinput
exec gunicorn glow_by_riri.wsgi --log-file -
