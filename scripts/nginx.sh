#!/usr/bin/env bash

# Reload systemd in case of new service files
sudo systemctl daemon-reexec

# Remove default Nginx config (if any)
sudo rm -f /etc/nginx/conf.d/default.conf

# Ensure conf.d directory exists
sudo mkdir -p /etc/nginx/conf.d

# Copy custom server block config
sudo cp /home/ec2-user/SportsMeetApplication/nginx/nginx.conf /etc/nginx/conf.d/sportsmeet.conf
echo "✅ Copied server block to /etc/nginx/conf.d/sportsmeet.conf"

# Test Nginx configuration
sudo nginx -t

# If config is valid, restart Nginx
if [ $? -eq 0 ]; then
    sudo systemctl restart nginx
    echo "✅ Nginx restarted successfully."
else
    echo "❌ Nginx configuration test failed. Please fix it."
    exit 1
fi
