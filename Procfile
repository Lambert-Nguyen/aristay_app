web: gunicorn backend.wsgi --chdir aristay_backend --log-file - --bind 0.0.0.0:$PORT
release: python aristay_backend/manage.py migrate