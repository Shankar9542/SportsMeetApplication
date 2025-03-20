#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "Updating package list..."
sudo apt update -y

echo "Installing required packages..."
sudo apt install -y libpq-dev gcc python3-dev python3-venv

# Ensure virtualenv is installed
if ! command -v virtualenv &> /dev/null; then
    echo "Installing virtualenv..."
    python3 -m pip install --user virtualenv
fi

# Create virtual environment (if not exists)
if [ ! -d "/home/ubuntu/env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv /home/ubuntu/env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source /home/ubuntu/env/bin/activate

# Upgrade pip inside virtual environment
echo "Upgrading pip in virtual environment..."
pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "/home/ubuntu/requirements.txt" ]; then
    echo "Installing dependencies from /home/ubuntu/requirements.txt..."
    pip install -r /home/ubuntu/requirements.txt
else
    echo "Error: requirements.txt not found in /home/ubuntu/"
    exit 1
fi

echo "All dependencies installed successfully!"
