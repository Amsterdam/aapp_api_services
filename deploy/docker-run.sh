#!/usr/bin/env sh

set -u   # crash on missing env variables
set -e   # stop on any error
set -x   # print what we are doing

cd /app
uwsgi --ini uwsgi.ini
