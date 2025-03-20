#!/bin/bash
echo "Starting Gunicorn..."

cd /home/ubuntu/SPORTSAPPLICATION
source /home/ubuntu/env/bin/activate

exec gunicorn --workers 3 --bind 0.0.0.0:8000 SportMeet.wsgi:application --log-file /home/ubuntu/gunicorn.log 2>&1
