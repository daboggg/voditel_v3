import os

from .settings import *

DEBUG = int(os.environ.get("DEBUG", default=0))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db/db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
#         'PORT': os.getenv('POSTGRES_PORT', 5432),
#         'USER': os.getenv('POSTGRES_USER', 'daboggg'),
#         'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
#         'NAME': os.getenv('POSTGRES_DB', "db01")
#     }
# }

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", default=[]).split(" ")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = "smtp.yandex.ru"
EMAIL_PORT = 465
EMAIL_HOST_USER = "zvovan77@yandex.ru"
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = True

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_ADMIN = EMAIL_HOST_USER