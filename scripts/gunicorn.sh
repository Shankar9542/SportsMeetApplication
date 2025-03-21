#!/bin/bash

# Define Gunicorn process name and log file
APP_NAME="myapp"  # Change this to your app name
GUNICORN_CMD="/usr/bin/gunicorn"  # Adjust if Gunicorn is installed elsewhere
LOG_FILE="/var/log/gunicorn.log"
SOCKET_FILE="/tmp/gunicorn.sock"

echo "Stopping existing Gunicorn process..."
pkill -f "gunicorn" || echo "No Gunicorn process found."

# Wait for the process to stop completely
sleep 3

echo "Starting Gunicorn process..."
cd /home/ubuntu/SPORTSAPPLICATION  # Change this to your app directory

# Start Gunicorn
$GUNICORN_CMD --workers 3 --bind unix:$SOCKET_FILE wsgi:app > $LOG_FILE 2>&1 &

# Verify if Gunicorn started
if pgrep -f "gunicorn"; then
    echo "Gunicorn started successfully."
else
    echo "Failed to start Gunicorn!" >&2
    exit 1
fi
