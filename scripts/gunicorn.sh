#!/usr/bin/bash

# Stop any existing Gunicorn process (owned by the 'ubuntu' user)
if pgrep -u ubuntu -f gunicorn; then
    echo "Stopping existing Gunicorn process..."
    pkill -u ubuntu -f gunicorn
    sleep 2
fi

# Navigate to the project directory
cd /home/ubuntu/SPORTSAPPLICATION || { echo "Failed to navigate to project directory"; exit 1; }

# Activate the virtual environment
source /home/ubuntu/env/bin/activate

# Ensure Gunicorn socket file is removed (avoids potential conflicts)
rm -f /home/ubuntu/SPORTSAPPLICATION/gunicorn.sock

# Start Gunicorn with correct user permissions in the background
exec gunicorn --workers 3 --bind unix:/home/ubuntu/SPORTSAPPLICATION/gunicorn.sock SportMeet.wsgi:application --daemon

# Confirm if Gunicorn started successfully
if [[ $? -eq 0 ]]; then
    echo "Gunicorn started successfully."
else
    echo "Failed to start Gunicorn!"
    exit 1
fi
