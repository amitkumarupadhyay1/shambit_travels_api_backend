web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:$PORT --workers 3 backend.wsgi:application
release: python manage.py migrate