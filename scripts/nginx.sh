#!/usr/bin/bash

sudo systemctl daemon-reload
sudo rm -f /etc/nginx/sites-enabled/default

# Copy the correct Nginx config
sudo cp /home/ubuntu/SPORTSAPPLICATION/nginx/nginx.conf /etc/nginx/sites-available/SportMeet

# Create a symlink to enable it
sudo ln -s /etc/nginx/sites-available/SportMeet /etc/nginx/sites-enabled/

# Add www-data to ubuntu group
sudo gpasswd -a www-data ubuntu

# Test Nginx config before restarting
sudo nginx -t

# Restart Nginx if the test is successful
if [ $? -eq 0 ]; then
    sudo systemctl restart nginx
else
    echo "Nginx configuration test failed. Check the config."
    exit 1
fi
