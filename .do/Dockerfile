FROM ghcr.io/commonknowledge/banmarchive:5d3ee3d2b70dada4eb4c79e554c9b90afd7c3014
RUN [ $COLLECTSTATIC == 1 ] && SKIP_DB=1 SECRET_KEY=dummy python manage.py collectstatic --noinput --clear
