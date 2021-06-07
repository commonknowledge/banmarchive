# Use an official Python runtime based on Debian 10 "buster" as a parent image.
FROM ghcr.io/commonknowledge/do-app-baseimage-django-node:latest

# Install the project requirements and build.
COPY --chown=app:app .bin/install.sh requirements.txt package.json yarn.lock .
RUN SKIP_MIGRATE=1 bash install.sh

# Copy the rest of the sources over
COPY --chown=app:app . .
ENV DJANGO_SETTINGS_MODULE=banmarchive.settings.production \
    NODE_ENV=production

RUN bash .bin/build.sh
