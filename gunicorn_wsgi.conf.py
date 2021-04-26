from pathlib import Path

_this_file = Path(__file__).resolve()
DIR_REPO = _this_file.parent.resolve()

accesslog = None
bind = f"127.0.0.1:8000"
capture_output = False
chdir = DIR_REPO.as_posix()
disable_redirect_access_to_syslog = True
graceful_timeout = 300
loglevel = "info"
max_requests = 200
max_requests_jitter = 20
pythonpath = DIR_REPO.as_posix()
reload = False
syslog = False
timeout = graceful_timeout * 2
worker_class = "sync"
workers = 1
