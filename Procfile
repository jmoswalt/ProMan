collectstatic: python manage.py collectstatic --dry-run --noinput
syncdb: python manage.py syncdb --noinput
web: gunicorn proman.wsgi -b 0.0.0.0:$PORT