#!/bin/bash

# Define the application directory
APP_DIR="/home/ec2-user/SportsMeetApplication"

# Activate virtual environment (if you have one)
cd $APP_DIR
source /home/ec2-user/env/bin/activate

# Stop existing services (e.g., Gunicorn or any running app service)
echo "Stopping Gunicorn..."
sudo systemctl stop gunicorn

# Pull the latest code (optional, if you use git for deployment)
echo "Pulling latest code from repository..."
git pull origin main

# Install or update Python dependencies
echo "Installing dependencies..."
pip install -r $APP_DIR/requirements.txt

# Run migrations (for Django apps)
echo "Running database migrations..."
python manage.py migrate

# Collect static files (for Django apps)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Restart Gunicorn (or other services you use)
echo "Starting Gunicorn..."
sudo systemctl start gunicorn

# Optionally, restart other services (e.g., Nginx, Celery, etc.)
# sudo systemctl restart nginx
# sudo systemctl restart celery

echo "Deployment completed successfully!"
