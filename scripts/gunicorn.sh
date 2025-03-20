#!/bin/bash
echo "Starting Gunicorn..."

cd /home/ubuntu/SPORTSAPPLICATION || exit  
source /home/ubuntu/env/bin/activate  

exec gunicorn --chdir /home/ubuntu/SPORTSAPPLICATION --workers 3 --bind 0.0.0.0:8000 SportMeet.wsgi:application --log-file - 2>&1
