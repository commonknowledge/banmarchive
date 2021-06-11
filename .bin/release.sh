set -e

python manage.py migrate
python manage.py regenerate_thumbnails
python manage.py reindex_pdfs
python manage.py update_index