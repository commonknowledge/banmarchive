set -e

if [ "$SKIP_YARN" != "1" ]; then
  yarn webpack
fi

SKIP_DB=1 SECRET_KEY=dummy poetry run python manage.py collectstatic --noinput --clear
