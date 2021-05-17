import urllib3
from .base import *
from urllib.parse import urlparse

DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
BASE_URL = os.getenv('BASE_URL')
ALLOWED_HOSTS = [urlparse(BASE_URL).netloc]

try:
    from .local import *
except ImportError:
    pass
