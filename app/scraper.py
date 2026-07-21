import httpx
import trafilatura
from datetime import datetime, UTC

USER_AGENT = "ReadItLaterBot/0.1 (personal project)"


async def scrape_url(link: str) -> dict:
    """
    Fetches a URL and extracts article content via trafilatura.
    Always returns a dict with at least `status`; on success it also
    includes the scraped fields, on failure it includes `failure_reason`.
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, # Ensures short links or redirected URLs (HTTP 301/302) are followed automatically
            timeout=10.0, # Cancels the request if the web page takes longer than 10 seconds to respond.
            headers={"User-Agent": USER_AGENT}, # Attaches the custom user agent declared earlier.
        ) as client:
            response = await client.get(link) # Sends the HTTP GET request asynchronously and pauses execution until the response arrives
            response.raise_for_status() # Checks if the server returned an error HTTP code (like 404 Not Found or 500 Server Error). If it did, it raises an exception
    except httpx.HTTPStatusError as e:
        # Catches HTTP error responses (e.g., 404, 403, 500) raised by raise_for_status().
        # Instead of crashing, it returns a clear error dictionary with the specific status code
        return {
            "status": "failed",
            "failure_reason": f"Site returned HTTP {e.response.status_code}",
        }
    except httpx.RequestError as e:
        # Catches connection issues (e.g., DNS resolution failures, connection timeouts, bad SSL certificates)
        #  and returns a formatted failure dictionary with the underlying error class name.
        return {
            "status": "failed",
            "failure_reason": f"Could not reach the site ({type(e).__name__})",
        }

    # Passes the raw HTML text (response.text) to trafilatura to parse out the core content
    extracted = trafilatura.bare_extraction(
        response.text,
        with_metadata=True, # Instructs trafilatura to look for titles, authors, and publication dates
        output_format="html", # Asks trafilatura to preserve basic HTML formatting (like paragraphs, bolding, lists) in the main body
        include_images=True, # Retains image tags present within the main article text.
        url=link, # Helps trafilatura resolve relative image links into absolute URLs
    )

    # Checks if trafilatura failed to find meaningful text (e.g., if the URL points to an image, a blank page, or a heavy JavaScript application without pre-rendered text)
    if not extracted or not extracted.get("text"):
        return {
            "status": "failed",
            "failure_reason": "Could not extract article content from this page",
        }

    # Getting time the article was published at 
    published_at = None
    if extracted.get("date"):
        try:
            published_at = datetime.fromisoformat(extracted["date"])
        except ValueError:
            pass  # leave published_at as None if the date format is unexpected

    word_count = len((extracted.get("text") or "").split()) # Calculating word count
    reading_time_minutes = max(1, round(word_count / 200))  # Calculating read time at a ~200 wpm average

    return {
        "status": "ready",
        "title": extracted.get("title"),
        "author": extracted.get("author"),
        "description": extracted.get("description"),
        "published_at": published_at,
        "hero_image_url": extracted.get("image"),
        "content_html": extracted.get("text"),  # NOT sanitized yet — step 6
        "reading_time_minutes": reading_time_minutes,
        "scraped_at": datetime.now(UTC),
    }