import logging
import re
from urllib.parse import quote_plus, urljoin
from playwright.async_api import Page
from helpers import (
    DOWNLOAD_DIR,
    SOURCES_SITE_BROWSE_URL,
    SOURCES_SITE_DOWNLOAD_URL,
    SOURCES_SITE_LOGIN_URL,
    SOURCES_SITE_PASSWORD,
    SOURCES_SITE_URL,
    SOURCES_SITE_USERNAME,
)
from services.local import crop_poster
from utils.browser import run_with_page



async def sources_site_login(
    page: Page | None = None,
) -> str:
    """Perform login on the website."""
    SOURCES_SITE_USERNAME
    SOURCES_SITE_PASSWORD

    if not SOURCES_SITE_USERNAME or not SOURCES_SITE_PASSWORD:
        raise ValueError(
            "Missing credentials. Set SOURCES_SITE_USERNAME/SOURCES_SITE_PASSWORD in env or .env file."
        )
    
    if page is None:
        return await run_with_page(
            lambda active_page: sources_site_login(SOURCES_SITE_USERNAME, SOURCES_SITE_PASSWORD, active_page),
            headless=True,
        )

    # If not redirected to login page, assume already logged in
    if "login.php" not in page.url:
        logging.info("Already logged in, skipping login step.")
        return "Already logged in"

    logging.info("Attempting to log in...")

    # Navigate to login page
    await page.goto(SOURCES_SITE_LOGIN_URL, wait_until="domcontentloaded")

    # Fill login form
    await page.fill("input[name='username']", SOURCES_SITE_USERNAME)
    await page.fill("input[name='password']", SOURCES_SITE_PASSWORD)

    # Submit form
    await page.locator("button[type='submit'], input[type='submit']").first.click()

    # Wait for page transition after login attempt.
    await page.wait_for_load_state("networkidle")

    if "login.php" in page.url:
        return "Login failed. Check credentials or site state."

    logging.info("Login successful.")
    return "Login successful"


async def get_poster(title: str) -> dict:
    """Search for a poster for the specified title."""

    async def _run(page: Page) -> dict:
        search_url = f"https://www.themoviedb.org/search?query={quote_plus(title)}"
        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        # Dismiss cookie consent banner if present.
        try:
            await page.locator(
                "button.cookie_light_accept, button#onetrust-accept-btn-handler, [aria-label='Accept']"
            ).first.click(timeout=3000)
            await page.wait_for_load_state("networkidle")
        except Exception:
            pass

        # Click the first movie/tv result card.
        await page.locator("a.result").first.click()
        await page.wait_for_load_state("networkidle")

        img = page.locator("img.poster").first
        await img.wait_for(timeout=2000)
        poster_src = await img.get_attribute("src")
        if not poster_src:
            raise RuntimeError("Poster source not found on TMDB page.")

        poster_name = poster_src.split("/")[-1]
        poster_url = f"https://www.themoviedb.org/t/p/original/{poster_name}"
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        output_path = DOWNLOAD_DIR / f"{safe_title}.jpg"

        response = await page.context.request.get(poster_url)
        if not response.ok:
            raise RuntimeError(f"Poster download failed with status {response.status}.")

        output_path.write_bytes(await response.body())
        crop_poster(str(output_path))

        return {
            "title": title,
            "poster_url": poster_url,
            "saved_to": str(output_path),
        }

    return await run_with_page(_run, headless=True)


async def search_torrents(query: str, limit: int = 10) -> list[dict]:
    """Search sources_site and return top matching titles with links."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    async def _run(page: Page) -> list[dict]:
        result_limit = max(0, limit)
        encoded_query = quote_plus(query.strip())
        search_url = (
            f"{SOURCES_SITE_BROWSE_URL}?search={encoded_query}&cat=0&searchin=1&sort=2"
        )

        logging.info(f"Performing search with query: '{query}'")
        logging.info(f"Constructed search URL: {search_url}")

        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        await sources_site_login(page=page)
        if search_url not in page.url:
            await page.goto(search_url, wait_until="domcontentloaded")

        rows = page.locator("div.torrentrow")
        rows_count = await rows.count()
        results = []

        for idx in range(rows_count):
            if len(results) >= result_limit:
                break

            row = rows.nth(idx)
            link = row.locator('a[href*="details.php?id="]').first
            if await link.count() == 0:
                continue

            title_text = (await link.inner_text() or "").strip()
            href = await link.get_attribute("href") or ""
            href = urljoin(SOURCES_SITE_URL, href)

            # Keep size extraction scoped to the same row to avoid mismatches.
            size_locator = row.locator("font.small").filter(
                has_text=re.compile(r"(KB|MB|GB|TB)", re.IGNORECASE)
            ).first
            size_text = (await size_locator.inner_text() or "").strip() if await size_locator.count() else ""

            if title_text:
                results.append(
                    {
                        "title": title_text,
                        "url": href,
                        "size": size_text.replace("\n", " "),
                    }
                )

        logging.info(f"Found {len(results)} results (limit={result_limit}).")

        return results

    return await run_with_page(_run, headless=True)


async def get_torrent_source(link: str) -> dict:
    """Download an official source file from the specified link and return saved file info."""

    async def _run(page: Page) -> dict:
        await sources_site_login(page=page)

        torrent_id = link.split("id=", 1)[-1].split("&", 1)[0] if "id=" in link else None
        if not torrent_id:
            raise ValueError("Invalid torrent link: missing id parameter.")

        download_url = f"{SOURCES_SITE_DOWNLOAD_URL}?id={torrent_id}"
        logging.info(f"Downloading torrent from: {download_url}")

        # Use context request API so direct download endpoints do not fail navigation.
        response = await page.context.request.get(download_url)
        if not response.ok:
            raise RuntimeError(f"Download request failed with status {response.status}.")

        content_disposition = response.headers.get("content-disposition", "")
        filename_match = re.search(
            r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?',
            content_disposition,
        )
        filename = filename_match.group(1) if filename_match else f"{torrent_id}.torrent"

        output_path = DOWNLOAD_DIR / filename
        output_path.write_bytes(await response.body())

        return {
            "torrent_id": torrent_id,
            "filename": filename,
            "saved_to": str(output_path),
        }

    return await run_with_page(_run, headless=True)


async def search_subtitles(query: str) -> list[dict]:
    """
    Search for subtitles matching the query.
    """
    async def _run(page: Page) -> list[dict]:
        await page.goto("https://www.subtitlecat.com/")
        await page.get_by_role("textbox", name="Search subtitle").click()
        await page.get_by_role("textbox", name="Search subtitle").fill(query)
        await page.get_by_role("button", name="Search").click()

        await page.wait_for_load_state("networkidle")


        items = page.locator("tr td a[href*='subs/']")
        results = []

        count = await items.count()

        for i in range(count):
            link = items.nth(i)
            text = await link.text_content()

            href = await link.get_attribute("href")

            results.append({
                "title": text.strip(),
                "url": urljoin(page.url, href),
            })

        return results

    return await run_with_page(_run, headless=True)


async def download_subtitle(link: str) -> dict:
    """
    Download the subtitle file from the specified link and return saved file info.
    """
    if not link or not link.strip():
        raise ValueError("Subtitle link cannot be empty.")

    async def _run(page: Page) -> dict:
        subtitle_page_url = link.strip()
        await page.goto(subtitle_page_url, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        # English download button used by subtitlecat pages.
        download_trigger = page.locator("#download_en")
        
        async with page.expect_download() as download_info:
            await download_trigger.click()

        download = await download_info.value
        filename = download.suggested_filename or "subtitle.srt"
        output_path = DOWNLOAD_DIR / filename
        await download.save_as(str(output_path))

        return {
            "source_url": subtitle_page_url,
            "filename": filename,
            "saved_to": str(output_path),
        }

    return await run_with_page(_run, headless=True)

