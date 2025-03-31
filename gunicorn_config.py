# Gunicorn Configuration File for IELTS Productive
# Updated for Azure Web App deployment - 2025

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes - optimized for Azure
workers = 2  # Reduced from CPU-based calculation for memory efficiency
worker_class = "gthread"  # Changed from sync to gthread for better concurrency
threads = 4  # Added explicit thread count
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "debug"  # Changed to debug for better troubleshooting
capture_output = True
enable_stdio_inheritance = True

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

# Memory management
max_requests = 1000
max_requests_jitter = 50
worker_tmp_dir = '/tmp'  # Use /tmp for worker temporary files
