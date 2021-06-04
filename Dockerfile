# Use an official Python runtime based on Debian 10 "buster" as a parent image.
FROM python:3.8.1-slim-buster

# Add user that will be used in the container.
RUN useradd wagtail

# Port used by this container to serve HTTP.
EXPOSE 80

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. Set PORT variable that is used by Gunicorn. This should match "EXPOSE"
#    command.

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Set this directory to be owned by the "wagtail" user.
RUN chown wagtail:wagtail /app

# Install machine dependencies
RUN apt-get update
RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash
RUN apt-get install -y nodejs

COPY .bin/prepare.sh /app/.bin/prepare.sh
RUN bash /app/.bin/prepare.sh

# Copy the source code of the project into the container.
RUN mkdir -p /home/wagtail && chown wagtail:wagtail /home/wagtail

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Install the project requirements and build.
COPY --chown=wagtail:wagtail .bin/install.sh requirements.txt package.json yarn.lock .
RUN SKIP_MIGRATE=1 bash install.sh

# Copy the rest of the sources over
COPY --chown=wagtail:wagtail . .
ENV PYTHONUNBUFFERED=1 \
    PORT=80 \
    DJANGO_SETTINGS_MODULE=banmarchive.settings.production \
    NODE_ENV=production \
    PATH=/home/wagtail/.local/bin:$PATH

RUN bash .bin/build.sh