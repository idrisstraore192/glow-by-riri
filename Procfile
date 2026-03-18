release: python manage.py migrate && python manage.py createsuperuser --noinput || true && python manage.py seed_products
web: gunicorn glow_by_riri.wsgi --log-file -
