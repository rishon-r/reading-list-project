from celery import Celery

# Instantiating the Celery Application
# - "reading_list": The name of the main module namespace for identifying tasks.
# - broker: Redis running on port 6379, DB 0. Holds the queue of pending tasks.
# - backend: Redis running on port 6379, DB 1. Stores results/status of completed tasks.
# Note: Using separate DBs (/0 and /1) keeps queue data and result data clean.
celery_app = Celery(
    "reading_list",
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

'''
HOW CELERY WORKS IN MY SYSTEM:

Your FastAPI app acts as the Celery client: 
calling .delay() on scrape_read_task serializes the task name and the read_id argument
into a message and pushes it onto Redis, which serves as the broker (the queue),
then returns immediately without waiting. Separately, a long-running Celery worker process 
continuously pulls messages off that queue and executes the matching task function — 
potentially several at once, depending on its concurrency/pool settings,
rather than strictly one at a time.
As for results: Celery can store task return values in a Redis-backed result backend,
but that's a separate, optional config from the broker, and it doesn't really apply here — 
scrape_read_task has no return statement (so it implicitly returns None), 
and its real "output" is the side effect of updating the Read row directly in your database 
(setting status, scraped fields, etc.). So your frontend isn't expected to poll Celery's
result backend at all — it just polls the Read row itself via a normal API call to see when status
flips from "scraping" to done.

'''
