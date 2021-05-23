set -e

pip install --user -r requirements.txt
yarn

if [ "$SKIP_MIGRATE" != "1" ]; then
  python manage.py migrate
fi
