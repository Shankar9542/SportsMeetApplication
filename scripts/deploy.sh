#!/usr/bin/env bash

# Activate virtual environment
source /home/ubuntu/env/bin/activate

# Change to project directory
cd /home/ubuntu/SPORTSAPPLICATION

# Run Django migrations
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

# Collect static files
python3 manage.py collectstatic --noinput

# Restart Gunicorn
sudo systemctl restart gunicorn
