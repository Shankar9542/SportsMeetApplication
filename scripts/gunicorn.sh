#!/usr/bin/bash
set -e

sudo cp /home/ubuntu/SPORTSAPPLICATION/gunicorn/gunicorn.socket /etc/systemd/system/
sudo cp /home/ubuntu/SPORTSAPPLICATION/gunicorn/gunicorn.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn.socket
sudo systemctl enable --now gunicorn.service
sudo systemctl restart gunicorn

# Optional: check status
sudo systemctl status gunicorn --no-pager
