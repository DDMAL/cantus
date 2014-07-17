#!/bin/bash

NAME="cantusdata"                                                   # name of the application
VIRTUAL_ENV=/Users/afogarty/Documents/st_gallen-dev/public/app_env  # name of virtual_env directory
DJANGODIR=/Users/afogarty/Documents/st_gallen-dev/public            # Django project directory
SOCKFILE=/tmp/cantusdata.sock                                       # we will communicte using this unix socket
USER=afogarty                                                       # the user to run as
GROUP=staff                                                         # the group to run as
NUM_WORKERS=3                                                       # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=cantusdata.settings                          # which settings file should Django use
DJANGO_WSGI_MODULE=cantusdata.wsgi                                  # WSGI module name

echo "Starting $NAME"

# Activate the virtual environment
cd $DJANGODIR
source ${VIRTUAL_ENV}/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
#RUNDIR=$(dirname $SOCKFILE)
#test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec ${VIRTUAL_ENV}/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --log-level=debug \
  --bind=unix:$SOCKFILE 