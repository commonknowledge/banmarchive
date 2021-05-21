set -e

yarn webpack
SKIP_DB=1 SECRET_KEY='[dummy]' python manage.py collectstatic --noinput --clear
rm -rf node_modules
