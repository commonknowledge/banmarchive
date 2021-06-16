set -e

pip install --user -r requirements.txt
yarn

if [ "$SKIP_MIGRATE" != "1" ]; then
  python manage.py migrate
  python manage.py preseed_transfer_table auth wagtailcore wagtailimages.image wagtaildocs
  python manage.py createsuperuser
fi
