import os

os.system('git push heroku master')
os.system('heroku run:detached python manage.py collectstatic')
os.system('heroku run python manage.py syncdb')