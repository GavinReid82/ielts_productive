#!/bin/bash

# Create necessary directories
mkdir -p /home/LogFiles
mkdir -p /tmp/flask_session
mkdir -p /tmp/uploads

# Set permissions
chmod 755 /home/LogFiles
chmod 755 /tmp/flask_session
chmod 755 /tmp/uploads

# Start Gunicorn
gunicorn -c gunicorn_config.py run:app 