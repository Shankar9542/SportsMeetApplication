#!/usr/bin/env bash

#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "Updating package list..."
sudo apt update -y

echo "Installing PostgreSQL development libraries..."
sudo apt install -y libpq-dev gcc python3-dev

echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing dependencies..."
pip install psycopg2-binary  # Use precompiled binary package
pip install -r requirements.txt

virtualenv /home/ubuntu/env
source /home/ubuntu/env/bin/activate
pip install -r /home/ubuntu/SPORTSAPPLICATION/requirements.txt