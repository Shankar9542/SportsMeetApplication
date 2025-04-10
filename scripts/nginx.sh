#!/usr/bin/env bash

# Reload systemd in case of new service files
sudo systemctl daemon-reexec

# Remove default Nginx config (if any)
sudo rm -f /etc/nginx/conf.d/default.conf

# Copy your custom Nginx configuration
sudo cp /home/ec2-user/SPORTSAPPLICATION/nginx/nginx.conf /etc/nginx/conf.d/sportmeet.conf

# Optional: Change permissions or ownership if needed
# sudo chown root:root /etc/nginx/conf.d/sportmeet.conf

# Test Nginx configuration
sudo nginx -t

# If config is valid, restart Nginx
if [ $? -eq 0 ]; then
    sudo systemctl restart nginx
    echo "Nginx restarted successfully."
else
    echo "❌ Nginx configuration test failed. Please fix it."
    exit 1
fi
