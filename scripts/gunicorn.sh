#!/usr/bin/bash

# Stop any existing Gunicorn process (with sudo if needed)
sudo pkill -f gunicorn || true

# Wait for processes to fully terminate
sleep 2

# Navigate to the project directory
cd /home/ubuntu/SPORTSAPPLICATION || exit

# Activate the virtual environment
source /home/ubuntu/env/bin/activate

# Start Gunicorn with proper user permissions
exec gunicorn --workers 3 --bind 0.0.0.0:8000 wsgi:application --daemon --user=ubuntu --group=ubuntu
