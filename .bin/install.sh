set -e

poetry run python -m spacy download en_core_web_md

poetry run python <<EOL
from nltk import download

download('stopwords')
download('punkt')
EOL

if [ "$SKIP_YARN" != "1" ]; then
  yarn
fi

if [ "$SKIP_MIGRATE" != "1" ]; then
  poetry run python manage.py migrate
  poetry run python manage.py preseed_transfer_table auth wagtailcore wagtailimages.image wagtaildocs publications search home banmarchive
  poetry run python manage.py createsuperuser
  touch banmarchive/settings/local.py
fi
