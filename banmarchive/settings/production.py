import urllib3
from .base import *
from urllib.parse import urlparse

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
BASE_URL = re.sub(r'/$', '', os.getenv('BASE_URL', ''))
PRIMARY_HOST = urlparse(BASE_URL).netloc
ALLOWED_HOSTS = ['*']  # Already handled by load balancer

REDIRECT_PERMANENT = os.getenv('REDIRECT_PERMANENT') == 'True'

DEFAULT_FILE_STORAGE = 'banmarchive.storages.DigitalOceanSpacesStorage'

AWS_S3_ADDRESSING_STYLE = 'virtual'
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')

ANYMAIL = {
    "MAILGUN_API_URL": os.getenv("MAILGUN_API_URL"),
    "MAILGUN_API_KEY": os.getenv('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": os.getenv('MAILGUN_SENDER_DOMAIN')
}
# or sendgrid.EmailBackend, or...
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
# if you don't already have this in settings
DEFAULT_FROM_EMAIL = f"noreply@{ANYMAIL['MAILGUN_SENDER_DOMAIN']}"
# ditto (default from-email for Django errors)
SERVER_EMAIL = f"admin@{ANYMAIL['MAILGUN_SENDER_DOMAIN']}"

try:
    from .local import *
except ImportError:
    pass

WAGTAILTRANSFER_SECRET_KEY = os.getenv('WAGTAILTRANSFER_SECRET_KEY', None)
