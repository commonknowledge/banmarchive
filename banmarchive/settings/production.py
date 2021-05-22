import urllib3
from .base import *
from urllib.parse import urlparse

DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
BASE_URL = os.getenv('BASE_URL')
ALLOWED_HOSTS = [urlparse(BASE_URL).netloc]

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
MEDIA_URL = os.getenv('MEDIA_URL')

ANYMAIL = {
    "MAILGUN_API_KEY": os.getenv('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": os.getenv('MAILGUN_SENDER_DOMAIN')
}
# or sendgrid.EmailBackend, or...
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
# if you don't already have this in settings
DEFAULT_FROM_EMAIL = f"noreply@{ANYMAIL['MAILGUN_SENDER_DOMAIN']}"
# ditto (default from-email for Django errors)
SERVER_EMAIL = f"admin@{ANYMAIL['MAILGUN_SENDER_DOMAIN']}"

DJANGO_LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'DEBUG')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': DJANGO_LOG_LEVEL,
        },
    },
}

try:
    from .local import *
except ImportError:
    pass
