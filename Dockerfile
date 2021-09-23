FROM ghcr.io/commonknowledge/do-app-baseimage-django-node:8b90c81ac3640d0b0e84f4730dbf5dcc4d2351f2 as assets

# Support system-provided packages
ENV PYTHONPATH /usr/lib/python3/dist-packages

# Install yarn dependencies, using external cache
COPY package.json yarn.lock .
RUN yarn install --frozen-lockfile

# Copy over static assets from host
COPY --chown=app:app . .

# Build static bundle
ENV NODE_ENV=production
RUN yarn webpack

FROM ghcr.io/commonknowledge/do-app-baseimage-django-node:8b90c81ac3640d0b0e84f4730dbf5dcc4d2351f2

# Support system-provided packages
ENV PYTHONPATH /usr/lib/python3/dist-packages

# Install the project requirements and build.
COPY --chown=app:app .bin/install.sh requirements.txt ./
RUN SKIP_MIGRATE=1 SKIP_YARN=1 bash install.sh

# Copy the rest of the sources over
COPY --chown=app:app . .
COPY --chown=app --from=assets /app/dist ./dist

ENV DJANGO_SETTINGS_MODULE=banmarchive.settings.production

RUN SKIP_YARN=1 bash .bin/build.sh
