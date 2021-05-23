set -e

apt-get update -y
apt-get install --yes --quiet --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    libmariadbclient-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    binutils \
    libproj-dev \
    gdal-bin

npm i -g yarn
