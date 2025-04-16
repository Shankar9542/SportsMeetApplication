#!/usr/bin/bash
set -e  # Exit on any error

echo "⚙️ Updating ALLOWED_HOSTS in settings.py..."
sed -i 's/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = \["192.168.0.110"\]/' /home/ec2-user/SportsMeetApplication/SportMeet/settings.py

echo "📂 Changing directory to Django project..."
cd /home/ec2-user/SportsMeetApplication

echo "📦 Activating virtual environment..."
source /home/ec2-user/env/bin/activate

echo "🔧 Running Django migrations..."
python manage.py makemigrations
python manage.py migrate

echo "🗂️ Collecting static files..."
yes | python manage.py collectstatic --noinput

echo "🔁 Restarting Gunicorn and Nginx..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "✅ Deployment complete!"
