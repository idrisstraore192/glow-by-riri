web: python manage.py migrate && python manage.py collectstatic --noinput && python manage.py seed_products && gunicorn glow_by_riri.wsgi --workers 2 --worker-class sync --timeout 60 --log-file -
