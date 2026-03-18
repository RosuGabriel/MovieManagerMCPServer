import logging
import re
import requests
from utils.browser import start_browser
from tools.local import crop_poster
from helpers import FILELIST_BROWSE_URL, FILELIST_DOWNLOAD_URL, FILELIST_LOGIN_URL, FILELIST_PASSWORD, FILELIST_USERNAME, FILELIST_URL, DOWNLOAD_DIR
from urllib.parse import quote_plus



def filelist_login(username: str | None = None, password: str | None = None) -> str:
    """
    Perform login on the website.
    """
    page = start_browser(headless=True)

    # If not redirected to login page, assume already logged in
    if "login.php" not in page.url:
        logging.info("Already logged in, skipping login step.")
        return "Already logged in"

    logging.info("Attempting to log in...")

    username = username or FILELIST_USERNAME
    password = password or FILELIST_PASSWORD

    if not username or not password:
        raise ValueError(
            "Missing credentials. Set FILELIST_USERNAME/FILELIST_PASSWORD in env or .env file."
        )

    # Navigate to login page
    page.goto(FILELIST_LOGIN_URL, wait_until="domcontentloaded")

    # Fill login form
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)

    # Submit form
    page.locator("button[type='submit'], input[type='submit']").first.click()

    # Wait for page transition after login attempt.
    page.wait_for_load_state("networkidle")

    if "login.php" in page.url:
        return "Login failed. Check credentials or site state."

    logging.info("Login successful.")
    return "Login successful"


def get_poster(title: str) -> dict:
    """Search for a poster for the specified title."""
    page = start_browser(headless=True)

    search_url = f"https://www.themoviedb.org/search?query={quote_plus(title)}"
    page.goto(search_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    # Dismiss cookie consent banner if present
    try:
        page.locator("button.cookie_light_accept, button#onetrust-accept-btn-handler, [aria-label='Accept']").first.click(timeout=3000)
        page.wait_for_load_state("networkidle")
    except Exception:
        pass

    # Click the first movie/tv result card
    page.locator("a.result").first.click()
    page.wait_for_load_state("networkidle")

    img = page.locator("img.poster").first
    img.wait_for(timeout=2000)
    poster_url = img.get_attribute("src")
    poster_name = poster_url.split("/")[-1]
    poster_url = f"https://www.themoviedb.org/t/p/original/{poster_name}"
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
    output_path = DOWNLOAD_DIR / (safe_title + ".jpg")

    r = requests.get(poster_url)
    r.raise_for_status()
    output_path.write_bytes(r.content)

    crop_poster(str(output_path))

    return {
        "title": title,
        "poster_url": poster_url,
        "saved_to": str(output_path)
    }


def search_source(query: str, limit: int = 10) -> list[dict]:
    """
    Search filelist and return top matching titles with links.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    page = start_browser(headless=True)
    encoded_query = quote_plus(query.strip())
    search_url = (
        f"{FILELIST_BROWSE_URL}?search={encoded_query}&cat=0&searchin=1&sort=2"
    )
    
    logging.info(f"Performing search with query: '{query}')")
    logging.info(f"Constructed search URL: {search_url}")
    
    page.goto(search_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    filelist_login()
    if search_url not in page.url:
        page.goto(search_url, wait_until="domcontentloaded")

    title_links = page.locator('span[data-html="true"] a[href*="details.php?id="]')
    sizes = page.locator('div[class="torrenttable"] span font').filter(has_text="GB")
    count = min(title_links.count(), max(0, limit))

    logging.info(f"Found {count} results.")

    results = []
    for idx in range(count):
        link = title_links.nth(idx)
        title = (link.inner_text() or "").strip()
        size = (sizes.nth(idx).inner_text() or "").strip()
        href = link.get_attribute("href") or ""
        href = FILELIST_URL + href.strip('/')
        if title:
            results.append({"title": title, "url": href, "size": size.replace("\n", " ")})

    return results


def get_torrent_source(link: str) -> dict:
    """
    Download an official source file from the specified link and return saved file info.
    """
    page = start_browser(headless=True)
    filelist_login()

    torrent_id = link.split("id=", 1)[-1].split("&", 1)[0] if "id=" in link else None
    if not torrent_id:
        raise ValueError("Invalid torrent link: missing id parameter.")

    download_url = f"{FILELIST_DOWNLOAD_URL}?id={torrent_id}"
    logging.info(f"Downloading torrent from: {download_url}")

    # Use context request API so direct download endpoints do not fail navigation.
    response = page.context.request.get(download_url)
    if not response.ok:
        raise RuntimeError(f"Download request failed with status {response.status}.")

    content_disposition = response.headers.get("content-disposition", "")
    filename_match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition)
    filename = filename_match.group(1) if filename_match else f"{torrent_id}.torrent"

    output_path = DOWNLOAD_DIR / filename
    output_path.write_bytes(response.body())

    return {
        "torrent_id": torrent_id,
        "filename": filename,
        "saved_to": str(output_path),
    }
