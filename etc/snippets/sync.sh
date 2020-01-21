#!/bin/bash

# Due to issues with using symlinks, the cantus folder 
# needs to be copied when the container is launched,
# this creates an ackward sync problem when developing for cantus

# Copy this script to /home/vagrant and run it,
# it will keep the files from the repository in sync
# with the files used by the django server to render the website

while true; do
    rsync -vur "/vagrant/" "/home/vagrant"
    sleep 1
done