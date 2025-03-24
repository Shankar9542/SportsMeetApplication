#!/usr/bin/env bash

set -e  # Exit if any command fails

# Define Variables
DB_USER="postgres"
DB_NAME="sai"
SQL_FILE="/home/ubuntu/database.sql"
VENV_PATH="/home/ubuntu/env"
PROJECT_DIR="/home/ubuntu/SPORTSAPPLICATION"

echo "🚀 Starting Deployment..."

# Activate Virtual Environment
source $VENV_PATH/bin/activate

# Change to Project Directory
cd $PROJECT_DIR

# Restore Database (Using Secure .pgpass File)
export PGPASSFILE="/home/ubuntu/.pgpass"
psql -U $DB_USER -d $DB_NAME -f $SQL_FILE

echo "✅ Database Restore Completed."

# Apply Django Migrations
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

echo "✅ Migrations Completed."

# Collect Static Files
python3 manage.py collectstatic --noinput

echo "✅ Static Files Collected."

# Restart Gunicorn Server
sudo systemctl restart gunicorn

echo "🎉 Deployment Completed Successfully!"
