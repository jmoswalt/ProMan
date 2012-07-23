import os

os.system('git push heroku master')
os.system('heroku run:detached collectstatic')
os.system('heroku run syncdb')