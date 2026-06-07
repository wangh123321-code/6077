import multiprocessing
import os

bind = "0.0.0.0:8000"

workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

worker_class = "uvicorn.workers.UvicornWorker"

worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", 2000))

timeout = int(os.getenv("GUNICORN_TIMEOUT", 30))

graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))

keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 65))

backlog = int(os.getenv("GUNICORN_BACKLOG", 4096))

max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 10000))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 1000))

preload_app = os.getenv("GUNICORN_PRELOAD", "true").lower() == "true"

reuse_port = True

chdir = "/app"

accesslog = os.getenv("GUNICORN_ACCESS_LOG", "/app/logs/gunicorn_access.log")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "/app/logs/gunicorn_error.log")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s %(L)s'

pidfile = os.getenv("GUNICORN_PID_FILE", "/var/run/gunicorn.pid")

raw_env = [
    "PYTHONUNBUFFERED=1",
    "PYTHONDONTWRITEBYTECODE=1",
]

def when_ready(server):
    server.log.info("Gunicorn is ready. Workers: %s, Worker class: %s", workers, worker_class)

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal (pid: %s)", worker.pid)

def child_exit(server, worker):
    server.log.info("Worker exited (pid: %s)", worker.pid)

def worker_exit(server, worker):
    server.log.info("Worker exited gracefully (pid: %s)", worker.pid)
