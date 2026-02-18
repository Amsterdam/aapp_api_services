# --- Networking ---
bind = "0.0.0.0:8000"
backlog = 64  # uwsgi: listen = 64

# --- Application ---
chdir = "/app"
wsgi_app = "core.asgi:application"

# --- Worker model ---
worker_class = "uvicorn.workers.UvicornWorker"
workers = 2
threads = 1
worker_connections = 500  # async-ready, ignored for sync views

# --- Timeouts ---
timeout = 30  # uwsgi: harakiri = 30
graceful_timeout = 60  # uwsgi: worker-reload-mercy = 60
keepalive = 2

# --- Recycling / memory ---
max_requests = 5000  # uwsgi: max-requests = 2000
max_requests_jitter = 500
max_worker_lifetime = 3600  # uwsgi: max-worker-lifetime = 3600

# worker_tmp_dir = "/tmp/shm"

# --- Logging ---
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# --- Process behavior ---
preload_app = False  # uwsgi: lazy-apps = true equivalent
daemon = False
