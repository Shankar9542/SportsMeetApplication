#!/usr/bin/bash

# Copy Gunicorn service files
sudo cp /home/ubuntu/SPORTSAPPLICATION/gunicorn/gunicorn.socket /etc/systemd/system/gunicorn.socket
sudo cp /home/ubuntu/SPORTSAPPLICATION/gunicorn/gunicorn.service /etc/systemd/system/gunicorn.service

# Reload systemd manager
sudo systemctl daemon-reload

# Enable and start Gunicorn service
sudo systemctl enable --now gunicorn.service

# Restart Gunicorn to apply changes
sudo systemctl restart gunicorn



# Check status
sudo systemctl status gunicorn --no-pager
