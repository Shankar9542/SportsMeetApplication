#!/bin/bash
set -e  # Exit on error

echo "Updating package list..."
sudo yum update -y

echo "Installing required development packages..."
sudo yum install -y gcc python3 python3-devel postgresql-devel

# Ensure pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip3..."
    sudo yum install -y python3-pip
fi

# Ensure virtualenv is installed
if ! command -v virtualenv &> /dev/null; then
    echo "Installing virtualenv..."
    pip3 install --user virtualenv
    export PATH=$PATH:/root/.local/bin:/home/ec2-user/.local/bin
fi

# Create virtual environment if not exists
if [ ! -d "/home/ec2-user/env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv /home/ec2-user/env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source /home/ec2-user/env/bin/activate

# Upgrade pip inside virtual environment
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "/home/ec2-user/SportsMeetApplication/requirements.txt" ]; then
    echo "Installing Python dependencies from requirements.txt..."
    pip install -r /home/ec2-user/SportsMeetApplication/requirements.txt
else
    echo "requirements.txt not found!"
fi
