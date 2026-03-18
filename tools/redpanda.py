import logging
from utils.browser import start_browser
from helpers import REDPANDA_CREATE_URL, REDPANDA_LOGIN_URL, REDPANDA_PASSWORD, REDPANDA_USERNAME



def redpanda_login(username: str | None = None, password: str | None = None) -> str:
    """
    Perform login on Redpanda website.
    """
    page = start_browser(headless=True)

    if "login" not in page.url:
        logging.info("Already logged in, skipping login step.")
        return "Already logged in"

    # Navigate to Redpanda login page
    page.goto(REDPANDA_LOGIN_URL, wait_until="domcontentloaded")

    username = username or REDPANDA_USERNAME
    password = password or REDPANDA_PASSWORD

    if not username or not password:
        raise ValueError(
            "Missing credentials. Set REDPANDA_USERNAME/REDPANDA_PASSWORD in env or .env file."
        )

    # Fill login form
    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill(REDPANDA_USERNAME)
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill(REDPANDA_PASSWORD)
    page.get_by_role("button", name="Login").click()

    # Wait for page transition after login attempt.
    page.wait_for_load_state("networkidle")

    if "login" in page.url:
        return "Login failed. Check credentials or site state."

    logging.info("Redpanda login successful.")
    return "Redpanda login successful"


def upload_media(mediaType: str = None, title: str = None, video_path: str = "", poster_path: str = "", description: str = "", release_date: str = "", seasonsNumber: str = None) -> dict:
    """Upload the processed media file to the website."""
    page = start_browser(headless=True)

    # Navigate to Redpanda create page
    page.goto(REDPANDA_CREATE_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    redpanda_login()
    page.goto(REDPANDA_CREATE_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    
    logging.info(f"Filling upload form with media type: {mediaType}, title: {title}, video path: {video_path}, poster path: {poster_path}, description: {description}, release date: {release_date}, seasons number: {seasonsNumber}")

    if not mediaType:
        raise ValueError("Media type is required.")
    page.get_by_label('Media Type').select_option(mediaType.title())

    if not title:
        raise ValueError("Title is required.")
    page.get_by_role("textbox", name="Title").click()
    page.get_by_role("textbox", name="Title").fill(title)
    
    if description:
        page.get_by_role("textbox", name="Description").click()
        page.get_by_role("textbox", name="Description").fill(description)

    if release_date:
        page.get_by_role("textbox", name="Release Date").fill(release_date)

    if poster_path:
        page.get_by_role("button", name="Poster").click()
        page.get_by_role("button", name="Poster").set_input_files(poster_path)
    
    if mediaType.lower() == "movie":
        if not video_path:
            raise ValueError("Video path is required for movies.")
        page.get_by_role("button", name="Video").click()
        page.get_by_role("button", name="Video").set_input_files(video_path)        
        page.get_by_role("button", name="Create Movie").click()
    elif mediaType.lower() == "series":
        if not seasonsNumber:
            raise ValueError("Seasons number is required for series.")
        page.get_by_role('spinbutton', name = 'Seasons').click()
        page.get_by_role('spinbutton', name = 'Seasons').fill(seasonsNumber)
        page.get_by_role("button", name="Create Series").click()

    return {
        "title": title,
        "status": "uploading"
    }