ARG VARIANT=3
FROM mcr.microsoft.com/vscode/devcontainers/python:0-3.9

ENV PYTHONUNBUFFERED 1

# Support system-provided packages
ENV PYTHONPATH /usr/lib/python3/dist-packages

# Update args in docker-compose.yaml to set the UID/GID of the "vscode" user.
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN if [ "$USER_GID" != "1000" ] || [ "$USER_UID" != "1000" ]; then groupmod --gid $USER_GID vscode && usermod --uid $USER_UID --gid $USER_GID vscode; fi

# [Option] Install Node.js
ARG INSTALL_NODE="true"
ARG NODE_VERSION="lts/*"
RUN if [ "${INSTALL_NODE}" = "true" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Install system dependencies
RUN curl https://raw.githubusercontent.com/commonknowledge/do-app-baseimage-django-node/439e8fecc8279266fcdd80942640000a1fb5a3ba/.bin/prepare.sh | /bin/bash