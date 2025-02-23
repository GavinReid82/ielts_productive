# Gunicorn Configuration File

limit_request_field_size = 0
limit_request_line = 0
timeout = 300  # Allow longer upload times
worker_connections = 1000  # Allow more simultaneous connections
workers = 3  # Adjust based on Azure App Service plan
bind = "0.0.0.0:8000"
