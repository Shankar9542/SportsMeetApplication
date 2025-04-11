#!/bin/bash
echo "Stopping Gunicorn process..."

# Look for a running Gunicorn process and stop it
pkill -f "gunicorn"

echo "Gunicorn stopped."
