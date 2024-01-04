FROM node:16-bullseye-slim as assets

# Install yarn dependencies, using external cache
RUN mkdir -p /app
WORKDIR /app

COPY package.json yarn.lock .
RUN yarn install --frozen-lockfile

# Copy over static assets from host
COPY --chown=app:app . .

# Build static bundle
ENV NODE_ENV=production
RUN yarn webpack

FROM python:3.9-slim-bullseye

RUN apt-get update -y
RUN apt-get install --yes --quiet --no-install-recommends \
    curl \
    git \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libmariadb-dev-compat \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    binutils \
    libproj-dev \
    gdal-bin \
    g++ \
    libgraphicsmagick++1-dev \
    libboost-python-dev \
    libtiff5-dev libopenjp2-7-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk \
    libharfbuzz-dev libfribidi-dev libxcb1-dev \
    python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils tesseract-ocr \
    flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev \
    libpoppler-cpp-dev pkg-config python3-dev ghostscript \
    python3-pgmagick

# Add user that will be used in the container.
RUN useradd app

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Set this directory to be owned by the "app" user.
RUN chown app:app /app

RUN mkdir -p /home/app
RUN chown app:app /home/app
USER app

# Install the project requirements and build.
RUN curl -sSL https://install.python-poetry.org/ | python -; \
  echo "export PATH="/home/app/.local/bin:$PATH" >> "$HOME/.profile"; \
  echo "export PATH="/home/app/.local/bin:$PATH" >> "$HOME/.bashrc"

COPY pyproject.toml poetry.lock .
RUN bash -c "poetry install"

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=banmarchive.settings.production \
    PATH=/home/app/.local/bin:$PATH \
    PORT=80

COPY --chown=app:app . .
COPY --chown=app --from=assets /app/dist ./dist

RUN SKIP_MIGRATE=1 SKIP_YARN=1 bash .bin/install.sh
RUN SKIP_YARN=1 bash .bin/build.sh
