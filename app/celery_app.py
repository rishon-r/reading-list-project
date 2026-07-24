from celery import Celery

# Instantiating the Celery Application
# - "tasks": The name of the main module namespace for identifying tasks.
# - broker: Redis running on port 6379, DB 0. Holds the queue of pending tasks.
# - backend: Redis running on port 6379, DB 1. Stores results/status of completed tasks.
# Note: Using separate DBs (/0 and /1) keeps queue data and result data clean.
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

# Additional Configurations
celery_app.conf.update(
    task_serializer="json",     # Convert task arguments to JSON before queueing
    result_serializer="json",   # Convert task return values to JSON for storage
    accept_content=["json"],    # Security rule: strictly process JSON payloads
    timezone="UTC",             # Enforce consistent UTC timestamps across servers
    enable_utc=True,
)

