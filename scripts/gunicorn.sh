#!/bin/bash
echo "Starting Gunicorn..."

# Change to your project directory
cd /home/ubuntu/SPORTSAPPLICATION || exit

# Activate virtual environment
source /home/ubuntu/env/bin/activate

# Run Gunicorn with Django's WSGI module
exec gunicorn --workers 3 --bind 0.0.0.0:8000 SportMeet.wsgi:application
