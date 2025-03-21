#!/bin/bash

echo "Starting Gunicorn..."
cd /home/ubuntu/SPORTSAPPLICATION || exit
source /home/ubuntu/env/bin/activate

# Kill any existing Gunicorn processes
pkill -f gunicorn

# Start Gunicorn
exec gunicorn --workers 3 --bind 0.0.0.0:8000 wsgi:application
