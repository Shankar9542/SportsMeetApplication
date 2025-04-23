#!/usr/bin/bash
set -e

echo ">>> Copying systemd files..."
sudo cp /home/ec2-user/SportsMeetApplication/gunicorn/gunicorn.socket /etc/systemd/system/
sudo cp /home/ec2-user/SportsMeetApplication/gunicorn/gunicorn.service /etc/systemd/system/

echo ">>> Reloading systemd..."
sudo systemctl daemon-reload

echo ">>> Enabling and starting gunicorn.socket..."
sudo systemctl enable --now gunicorn.socket

echo ">>> Enabling and starting gunicorn.service..."
sudo systemctl enable --now gunicorn.service

echo ">>> Restarting gunicorn..."
sudo systemctl restart gunicorn

echo ">>> Gunicorn status:"
sudo systemctl status gunicorn --no-pager
