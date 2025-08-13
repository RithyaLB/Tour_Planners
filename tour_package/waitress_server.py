# waitress_server.py
import os
import sys
from waitress import serve
import django
from django.core.wsgi import get_wsgi_application
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('logs/waitress.log'),
        logging.StreamHandler()
    ]
)

# Add your project directory to Python path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tour_package.settings')

# Setup Django
django.setup()

# Get WSGI application
application = get_wsgi_application()

if __name__ == '__main__':
    logging.info("Starting Waitress server on http://127.0.0.1:8000")
    serve(
        application,
        host='127.0.0.1',
        port=8000,
        threads=4,
        connection_limit=1000,
        cleanup_interval=30,
        channel_timeout=300,
        log_socket_errors=True,
        send_bytes=18000,
        recv_bytes=18000,
        asyncore_use_poll=True,
        backlog=1024,
        _quiet=False
        # Removed invalid 'task_dispatcher' parameter
    )