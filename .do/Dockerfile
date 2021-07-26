FROM ghcr.io/commonknowledge/banmarchive:4dd64afff742976132348b7bad4ce587afdb444b
RUN [  == 1 ] && SKIP_DB=1 SECRET_KEY=dummy python manage.py collectstatic --noinput --clear
