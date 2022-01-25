set -e

poetry run python manage.py migrate
poetry run python manage.py reindex_pdfs
