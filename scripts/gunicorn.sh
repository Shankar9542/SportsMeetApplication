#!/bin/bash
echo "Starting Gunicorn..."

# Change to your project directory
cd /home/ubuntu/SPORTSAPPLICATION  

# Activate virtual environment
source /home/ubuntu/env/bin/activate  

# Run Gunicorn with your app
exec /home/ubuntu/env/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 wsgi:app  # Adjust as needed
