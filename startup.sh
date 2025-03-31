#!/bin/bash

# Navigate to the application directory
cd /home/site/wwwroot

# Create necessary directories
mkdir -p /home/LogFiles
mkdir -p /tmp/uploads

# Set permissions
chmod 755 /home/LogFiles
chmod 755 /tmp/uploads

# Activate virtual environment
source antenv/bin/activate

# Install dependencies with memory optimization
pip install --no-cache-dir --no-deps -r requirements.txt

# Set environment variables
export FLASK_ENV=production
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/site/wwwroot
export GUNICORN_CMD_ARGS="--timeout 120 --workers 4 --threads 2 --worker-class gthread"

# Start Gunicorn with optimized settings
gunicorn -c gunicorn_config.py run:app --bind 0.0.0.0:8000 --timeout 120 --workers 4 --threads 2 --worker-class gthread 