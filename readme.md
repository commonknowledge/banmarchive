# Amiel Melburn Trust Internet Archive

An indexed and searchable online database of socialist and radical writings.

https://banmarchive-b96qj.ondigitalocean.app/


## Stack

* Django (fullstack django app, no js frontend)
* Bootstrap (css an' stuff)
* Wagtail (CMS, administration, editor workflows and storage)
* Webpack (asset pipeline)
* PostgreSQL (Database & search index)
* Digital Ocean App Platform (Compute, database hosting, object storage & CDN)


## Dev quickstart

### Easy mode: VSCode Dev Container

* Make sure you have Docker, VSCode, and the Remote Development extension installed.
* Open the repository in VSCode
* Wait for the dev container to build.
* Check your terminal and wait for your dev installation to bootstrap
* Run the following in your vscode terminal:

```bash
python manage.py createsuperuser
```

* Use vscode's 'run' command (usually aliased to F5) to run the app.


### Hard mode: Docker 

TODO. Or figure it out for yourself based on the .devcontainer dockerfile ;)


## Technical documentation

### Build process

This repository has a development dockerfile (.devcontainer/Dockerfile) and a production one (./Dockerfile).

They both run scripts in ./scripts to configure their environments and install dependencies:

* Base container configuration, which is run infrequently (installing apt packages, etc) should be configured in prepare.sh.
* Frequently-run scripts (installing pip packages, etc) should go in install.sh. The difference between these is that changing prepare.sh triggers a full rebuild of the development container, whereas install.sh is only run after the container is built.
* build.sh is the last thing run on deploy to production