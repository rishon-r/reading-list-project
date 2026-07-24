import httpx
import trafilatura
from datetime import datetime, UTC

USER_AGENT = "ReadItLaterBot/0.1 (personal project)"


async def scrape_url(link: str) -> dict:
    """
    Fetches a URL and extracts article content via trafilatura.
    Returns a dict with status and extracted metadata/content.
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=10.0,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = await client.get(link)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print("DEBUG: HTTPStatusError:", e)
        return {
            "status": "failed",
            "failure_reason": f"Site returned HTTP {e.response.status_code}",
        }
    except httpx.RequestError as e:
        print("DEBUG: RequestError:", e)
        return {
            "status": "failed",
            "failure_reason": f"Could not reach the site ({type(e).__name__})",
        }

    print("DEBUG: STATUS CODE:", response.status_code)
    print("DEBUG: HTML LENGTH:", len(response.text))

    # 1. Extract the main body as HTML
    content_html = trafilatura.extract(
        response.text,
        url=link,
        output_format="html",
        include_images=True,
        favor_recall=True,
    )

    # 2. Extract metadata (title, author, date, hero image)
    metadata = trafilatura.extract_metadata(response.text, default_url=link)

    # Verify content was successfully extracted
    if not content_html:
        return {
            "status": "failed",
            "failure_reason": "Could not extract article content from this page",
        }

    # Extract metadata properties safely
    title = metadata.title if metadata else None
    author = metadata.author if metadata else None
    description = metadata.description if metadata else None
    hero_image_url = metadata.image if metadata else None
    
    # Process publication date
    published_at = None
    if metadata and metadata.date:
        try:
            published_at = datetime.fromisoformat(metadata.date)
        except ValueError:
            pass

    # Compute word count & read time from the extracted body
    word_count = len(content_html.split())
    reading_time_minutes = max(1, round(word_count / 200))

    return {
        "status": "ready",
        "title": title,
        "author": author,
        "description": description,
        "published_at": published_at,
        "hero_image_url": hero_image_url,
        "content_html": content_html,  # Clean HTML string
        "reading_time_minutes": reading_time_minutes,
        "scraped_at": datetime.now(UTC),
    }