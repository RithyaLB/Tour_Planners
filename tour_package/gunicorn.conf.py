# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 100

# Logging
errorlog = "logs/gunicorn_error.log"
accesslog = "logs/gunicorn_access.log"
loglevel = "info"

# Process naming
proc_name = 'django_gunicorn'

# Daemonize the Gunicorn process
daemon = False