set -e

python manage.py migrate
python manage.py preseed_transfer_table auth wagtailcore wagtailimages.image wagtaildocs
python manage.py regenerate_thumbnails
python manage.py reindex_pdfs
python manage.py update_index
