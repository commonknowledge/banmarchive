set -e

pip install --user -r requirements.txt
python -m spacy download en_core_web_md
python <<EOL
from nltk import download

download('stopwords')
download('punkt')
EOL

if [ "$SKIP_YARN" != "1" ]; then
  yarn
fi

if [ "$SKIP_MIGRATE" != "1" ]; then
  python manage.py migrate
  python manage.py preseed_transfer_table auth wagtailcore wagtailimages.image wagtaildocs publications search home banmarchive
  python manage.py createsuperuser
  touch banmarchive/settings/local.py
fi
