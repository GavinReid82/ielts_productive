#!/bin/bash

# Navigate to the application directory
cd /home/site/wwwroot

# Create necessary directories
mkdir -p /home/LogFiles
mkdir -p /tmp/flask_session
mkdir -p /tmp/uploads

# Set permissions
chmod 755 /home/LogFiles
chmod 755 /tmp/flask_session
chmod 755 /tmp/uploads

# Install dependencies if needed
if [ ! -d "antenv" ]; then
    python -m venv antenv
fi
source antenv/bin/activate
pip install --no-cache-dir -r requirements.txt

# Start Gunicorn
gunicorn -c gunicorn_config.py run:app 