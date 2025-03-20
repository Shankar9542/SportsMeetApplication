#!/bin/bash
echo "Starting Gunicorn..."

# Change to your project directory
cd /home/ubuntu/SPORTSAPPLICATION  

# Activate virtual environment
source /home/ubuntu/env/bin/activate  

# Run Gunicorn with Django's WSGI module
exec /home/ubuntu/env/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 SportMeet.wsgi:application  # Update with your project name
