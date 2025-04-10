#!/usr/bin/bash
set -e  # Exit immediately on error

echo "⚙️ Updating ALLOWED_HOSTS..."
sed -i 's/\[\]/\["192.168.0.115"]/' /home/ec2-user/SPORTSAPPLICATION/SportMeet/settings.py

echo "📦 Running database migrations..."
cd /home/ec2-user/SPORTSAPPLICATION
source /home/ec2-user/env/bin/activate

python manage.py makemigrations
python manage.py migrate

echo "🗂️ Collecting static files..."
yes | python manage.py collectstatic

echo "🔁 Restarting Gunicorn and Nginx..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "✅ Deployment complete!"
