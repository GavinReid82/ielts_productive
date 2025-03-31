# Gunicorn Configuration File for IELTS Productive
# Updated for Azure Web App deployment - 2025

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 4  # Increased for Azure
worker_class = 'sync'
worker_connections = 1000
timeout = 300
keepalive = 2

# Logging
accesslog = '/home/LogFiles/gunicorn_access.log'
errorlog = '/home/LogFiles/gunicorn_error.log'
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
tmp_upload_dir = '/tmp/uploads'

# Debug
reload = False
reload_engine = 'auto'

# Azure specific
forwarded_allow_ips = '*'
secure_scheme_headers = {'X-FORWARDED-PROTOCOL': 'ssl', 'X-FORWARDED-PROTO': 'https', 'X-FORWARDED-SSL': 'on'}
