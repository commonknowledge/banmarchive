FROM ghcr.io/commonknowledge/do-app-baseimage-django-node@sha256:04130461fd163f935f2fd3ee9ed8c12c11dd91c11c6cfcc9342c013311e4a986 as assets

# Install yarn dependencies, using external cache
COPY package.json yarn.lock .
RUN yarn install --frozen-lockfile

# Copy over static assets from host
COPY --chown=app:app . .

# Build static bundle
ENV NODE_ENV=production
RUN yarn webpack

FROM ghcr.io/commonknowledge/do-app-baseimage-django-node@sha256:04130461fd163f935f2fd3ee9ed8c12c11dd91c11c6cfcc9342c013311e4a986

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