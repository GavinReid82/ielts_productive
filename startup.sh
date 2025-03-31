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

# Install dependencies if needed
pip install --no-cache-dir -r requirements.txt

# Set environment variables
export FLASK_ENV=production
export PYTHONUNBUFFERED=1

# Start Gunicorn
gunicorn -c gunicorn_config.py run:app 