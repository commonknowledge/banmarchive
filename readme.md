# Amiel Melburn Trust Internet Archive

An indexed and searchable online database of socialist and radical writings.

Staging: https://banmarchive.commonknowledge.dev/

## Stack

- Django (fullstack django app, no Javascript frontend)
- Bootstrap (css an' stuff)
- Wagtail (CMS, administration, editor workflows and storage)
- Webpack (asset pipeline)
- PostgreSQL (Database & search index)
- Digital Ocean App Platform (Compute, database hosting, object storage & CDN)

## Dev quickstart

### Easy mode: VSCode Dev Container

- Make sure you have Docker, VSCode, and the Remote Development extension installed.
- Open the repository in VSCode
- You should get a notification asking if you want to 'reopen in container'. Say yes.
  - If you don't get one, you should be able to 'reopen in container' via the command pallette
  - If you can't see an option to do that, make sure you have the Remote Development extension installed
- Wait for the dev container to build.
- Check your terminal and respond to any setup prompts it asks for
- Search for banmarchive/settings/local.py on lastpass and paste its contents into the corresponding local file
- Use vscode's 'run' command (usually aliased to F5) to run the app.
  - Make sure you use the 'App' configuration, which will start both the django app and the frontend build pipeline.
- Go to localhost:8000/admin
- Use the 'import' option on the left to seed the archive with content from the staging site.

### Hard mode: Using Dockerfiles

Figure it out for yourself based on the .devcontainer dockerfile and write it up here ;)

## Technical documentation

### Build process

This repository has a development dockerfile (.devcontainer/Dockerfile) and a production one (./Dockerfile).

They both run .bin in ./.bin to configure their environments and install dependencies:

- Base container configuration, which is run infrequently (installing apt packages, etc) should be configured in prepare.sh.
- Frequently-run .bin (installing pip packages, etc) should go in install.sh. The difference between these is that changing prepare.sh triggers a full rebuild of the development container, whereas install.sh is only run after the container is built.
- build.sh is the last thing run on deploy to production

## Notes

* New Reasoner's issues are divided into sections. Information about sections has not been migrated.
