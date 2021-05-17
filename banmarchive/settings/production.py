from .base import *

DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
BASE_URL = os.getenv('BASE_URL')

try:
    from .local import *
except ImportError:
    pass
