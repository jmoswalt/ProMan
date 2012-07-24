import os
from os import environ
import dj_database_url

PROJECT_ROOT = os.path.abspath('.')
ROOT_URLCONF = 'proman.urls'
WSGI_APPLICATION = 'proman.wsgi.application'

# Helper lambda for gracefully degrading environmental variables:
env = lambda e, d: environ[e] if environ.has_key(e) else d

# Load the .env file into the os.environ for secure information
try:
    env_file = open(os.path.join(PROJECT_ROOT, '.env'), 'r')
    for line in env_file.readlines():
        env_key = line.rstrip().split("=")[0]
        if env_key:
            # set the environment variable to the value with the start and
            # end quotes taken off.
            environ[env_key] = ''.join(line.rstrip().split("=")[1:])[1:-1]
    env_file.close()
except:
    # no .env file or errors in the file
    pass


# -------------------------------------- #
# DEBUG
# -------------------------------------- #
DEBUG = bool(env('DEBUG', False))
TEMPLATE_DEBUG = bool(env('TEMPLATE_DEBUG', DEBUG))


# -------------------------------------- #
# DATABASES
# -------------------------------------- #
# Databases uses dj_database_url to pull DATABASE_URL from the environment
DATABASES = {'default': dj_database_url.config(default='postgres://localhost')}


# -------------------------------------- #
# EMAIL
# -------------------------------------- #
EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', 587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', 'your_email@example.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# -------------------------------------- #
# TIME AND LANGUAGE
# -------------------------------------- #
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

LANG='en_US.UTF-8'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# -------------------------------------- #
# SITE ID
# -------------------------------------- #
SITE_ID = 1


# -------------------------------------- #
# UPLOADED MEDIA
# -------------------------------------- #
# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''


# -------------------------------------- #
# STATIC MEDIA
# -------------------------------------- #
# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = env('STATIC_URL', '/static/')

if DEBUG:
    STATIC_URL = '/static/'
else:
    STATICFILES_STORAGE = 's3_folder_storage.s3.StaticStorage'

# Admin media pulled from Django Grappelli
# Waiting on 1.4 compatibility
# ADMIN_MEDIA_PREFIX = STATIC_URL + "grappelli/"

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATIC_S3_PATH = env('STATIC_S3_PATH', 'static')

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', '')


# -------------------------------------- #
# SECRET KEY
# -------------------------------------- #
# Make this unique, and don't share it with anybody.
SECRET_KEY = env('SECRET_KEY', 'secret')


# -------------------------------------- #
# TEMPLATES
# -------------------------------------- #
# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "pm.context_processors.active_users",
    "pm.context_processors.app_settings",
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "templates"),
    os.path.join(PROJECT_ROOT, "pm", "templates"),
)


# -------------------------------------- #
# MIDDLEWARE
# -------------------------------------- #
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


# -------------------------------------- #
# APPS
# -------------------------------------- #
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.markup',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # Waiting on 1.4 compatibility
    # 'grappelli',
    'django.contrib.admin',
    'django.contrib.humanize',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'gunicorn',
    's3_folder_storage',
    'raven.contrib.django',
    'djcelery',
    'pm',
)

AUTH_PROFILE_MODULE = 'pm.Profile'

# -------------------------------------- #
# CELERY
# -------------------------------------- #
import djcelery
djcelery.setup_loader()
BROKER_URL = 'django://'


# -------------------------------------- #
# HARVEST INTEGRATIONS
# -------------------------------------- #
HV_URL = env('HV_URL', '')
HV_USER = env('HV_USER', '')
HV_PASS = env('HV_PASS', '')


# -------------------------------------- #
# SUGARCRM INTEGRATIONS
# -------------------------------------- #
SC_URL = env('SC_URL', '')
SC_USER = env('SC_USER', '')
SC_PASS = env('SC_PASS', '')


# -------------------------------------- #
# CACHE
# -------------------------------------- #
SITE_CACHE_KEY = "proman"

LOCAL_CACHE_PATH = env('LOCAL_CACHE_PATH', os.path.join(PROJECT_ROOT, "cache"))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': LOCAL_CACHE_PATH,
        'TIMEOUT': 60000000,
        'OPTIONS': {
            'MAX_ENTRIES': 10000000
        }
    }
}

MEMCACHE_SERVERS = env('MEMCACHE_SERVERS', '')

if MEMCACHE_SERVERS:
    CACHES = {
        'default': {
            'BACKEND': 'django_pylibmc.memcached.PyLibMCCache'
        }
    }

