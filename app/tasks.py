import asyncio # Standard library module that lets sync code run async coroutines (via asyncio.run())
from celery_app import celery_app # Imports the configured Celery application instance (where broker, backend, etc. are set up) from your celery_app module
from database import AsyncSessionLocal # Imports an async SQLAlchemy session factory — calling AsyncSessionLocal() gives you a new AsyncSession for talking to the database asynchronously
from scraper import scrape_url # Imports your async scraping function
import models
from sqlalchemy import select


@celery_app.task(name="scrape_read_task") # Registers this function as a Celery task named "scrape_read_task"
def scrape_read_task(read_id: int):
    """
    Celery entrypoint — must be a plain sync function (Celery doesn't
    natively support async task functions). We bridge into async code
    via asyncio.run() so we can reuse your existing async scrape_url()
    and async DB session.
    """

    # This is the sync-to-async bridge. asyncio.run():
    # Creates a new event loop
    # Runs the _do_scrape(read_id) coroutine to completion
    # Closes the loop

    # This lets the rest of the logic be written naturally with async/await (reusing your existing async DB session and scraper) even though Celery itself thinks it's calling a normal function
    asyncio.run(_do_scrape(read_id))


# The real worker coroutine, kept separate so it can use await freely
async def _do_scrape(read_id: int): 
    async with AsyncSessionLocal() as db:
        # Fetch the read row fresh in this new session/process
        result = await db.execute(select(models.Read).where(models.Read.id == read_id))
        read = result.scalars().first()

        if not read:
            # Defensive check: if the row was deleted between when the task was queued
            #  and when it actually ran, there's nothing to do — 
            # the task exits quietly rather than erroring
            return

        # Mark as scraping so the frontend polling sees the transition
        read.status = "scraping"
        await db.commit()

        try:
            scrape_result = await scrape_url(read.link)
        except Exception as exc:
            read.status = "failed"
            read.failure_reason = f"Unexpected error during scrape: {exc}"
            # optionally store the error message too, if your model has a field for it
            # read.error_message = str(exc)
            await db.commit()
            raise  # re-raise so Celery still logs/marks the task as failed


        # Apply whatever scrape_url returned (status, title, content_html, etc.)
        for field, value in scrape_result.items():
            setattr(read, field, value)

        await db.commit()

