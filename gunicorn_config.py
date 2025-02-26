# Gunicorn Configuration File for IELTS Productive
# Updated for Azure Web App deployment - 2025

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 3
worker_class = 'sync'
worker_connections = 1000
timeout = 300
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'ielts-productive'

# SSL
keyfile = None
certfile = None

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Debug
reload = False
reload_engine = 'auto'
