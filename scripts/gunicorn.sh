#!/bin/bash
echo "Starting Gunicorn..."
cd /home/ubuntu/SPORTSAPPLICATION  # Change this to your project directory
source /home/ubuntu/env/bin/activate
gunicorn --workers 3 --bind 0.0.0.0:8000 wsgi:app  # Update with your Gunicorn command
