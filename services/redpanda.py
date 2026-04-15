import logging
import re
from playwright.async_api import Page
from utils.helpers import (
    REDPANDA_CREATE_URL,
    REDPANDA_LOGIN_URL,
    REDPANDA_MEDIA_URL,
    REDPANDA_PASSWORD,
    REDPANDA_USERNAME,
)
from utils.browser import run_with_page
from services.local import process_subtitles



async def redpanda_login(
    username: str | None = None,
    password: str | None = None,
    page: Page | None = None,
) -> str:
    """Perform login on Redpanda website."""
    if page is None:
        return await run_with_page(
            lambda active_page: redpanda_login(username, password, active_page),
            headless=True,
        )

    if "login" not in page.url:
        logging.info("Already logged in, skipping login step.")
        return "Already logged in"

    # Navigate to Redpanda login page.
    await page.goto(REDPANDA_LOGIN_URL, wait_until="domcontentloaded")

    username = username or REDPANDA_USERNAME
    password = password or REDPANDA_PASSWORD

    if not username or not password:
        raise ValueError(
            "Missing credentials. Set REDPANDA_USERNAME/REDPANDA_PASSWORD in env or .env file."
        )

    # Fill login form.
    await page.get_by_role("textbox", name="Email").click()
    await page.get_by_role("textbox", name="Email").fill(username)
    await page.get_by_role("textbox", name="Password").click()
    await page.get_by_role("textbox", name="Password").fill(password)
    await page.get_by_role("button", name="Login").click()

    await page.wait_for_load_state("networkidle")

    if "login" in page.url:
        return "Login failed. Check credentials or site state."

    logging.info("Redpanda login successful.")
    return "Redpanda login successful"


async def upload_media(
    mediaType: str = None,
    title: str = None,
    video_path: str = "",
    poster_path: str = "",
    description: str = "",
    release_date: str = "",
    seasonsNumber: str = None,
) -> dict:
    """Upload the processed media file to the website."""

    async def _run(page: Page) -> dict:
        await page.goto(REDPANDA_CREATE_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
        await redpanda_login(page=page)
        await page.goto(REDPANDA_CREATE_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        logging.info(
            "Filling upload form with media type: %s, title: %s, video path: %s, "
            "poster path: %s, description: %s, release date: %s, seasons number: %s",
            mediaType,
            title,
            video_path,
            poster_path,
            description,
            release_date,
            seasonsNumber,
        )

        if not mediaType:
            raise ValueError("Media type is required.")
        if not title:
            raise ValueError("Title is required.")

        await page.get_by_label("Media Type").select_option(mediaType.title())

        await page.get_by_role("textbox", name="Title").click()
        await page.get_by_role("textbox", name="Title").fill(title)

        if description:
            await page.get_by_role("textbox", name="Description").click()
            await page.get_by_role("textbox", name="Description").fill(description)

        if release_date:
            await page.get_by_role("textbox", name="Release Date").fill(release_date)

        if poster_path:
            await page.get_by_role("button", name="Poster").set_input_files(poster_path)

        if mediaType.lower() == "movie":
            if not video_path:
                raise ValueError("Video path is required for movies.")
            await page.get_by_role("button", name="Video").set_input_files(video_path)
            await page.get_by_role("button", name="Create Movie").click()
        elif mediaType.lower() == "series":
            if not seasonsNumber:
                raise ValueError("Seasons number is required for series.")
            await page.get_by_role("spinbutton", name="Seasons").click()
            await page.get_by_role("spinbutton", name="Seasons").fill(seasonsNumber)
            await page.get_by_role("button", name="Create Series").click()

        return {
            "title": title,
            "status": "uploading",
        }

    try:
        return await run_with_page(_run, headless=True)
    except Exception as e:
        logging.error("Failed to upload media: %s", e)
        return {
            "title": title,
            "status": "error",
            "message": str(e),
        }


async def upload_episode(
    series_title: str = None,
    season_number: str = None,
    episode_number: str = None,
    episode_title: str = None,
    video_path: str = "",
    poster_path: str = "",
    description: str = "",
    release_date: str = "",
) -> dict:
    """Upload the processed episode file of a series to the website."""

    async def _run(page: Page) -> dict:
        await page.goto(REDPANDA_MEDIA_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
        await redpanda_login(page=page)
        await page.goto(REDPANDA_MEDIA_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        logging.info(
            f"Filling upload form for episode: {episode_number}, series: {series_title}, season number: {season_number}, video path: {video_path}, "
            f"poster path: {poster_path}, description: {description}, release date: {release_date}"
        )

        if not series_title:
            raise ValueError("Series title is required.")
        if not season_number:
            raise ValueError("Season number is required.")
        if not episode_number:
            raise ValueError("Episode number is required.")
        if not video_path:
            raise ValueError("Video path is required for episodes.")

        await page.get_by_role("link", name=re.compile(series_title, re.IGNORECASE)).click()
        await page.get_by_role("link", name="Add Episode").click()

        if episode_title:
            await page.get_by_role("textbox", name="Title").click()
            await page.get_by_role("textbox", name="Title").fill(episode_title)

        await page.get_by_role("spinbutton", name="Season").click()
        await page.get_by_role("spinbutton", name="Season").fill(season_number)

        await page.get_by_role("spinbutton", name="Episode Number").click()
        await page.get_by_role("spinbutton", name="Episode Number").fill(episode_number)

        if description:
            await page.get_by_role("textbox", name="Description").click()
            await page.get_by_role("textbox", name="Description").fill(description)

        if release_date:
            await page.get_by_role("textbox", name="Release Date").fill(release_date)

        await page.get_by_role("button", name="Video").set_input_files(video_path)

        if poster_path:
            await page.get_by_role("button", name="Poster").set_input_files(poster_path)

        await page.get_by_role("button", name="Create Episode").click()

        return {
            "title": series_title,
            "season": season_number,
            "episode": episode_number,
            "status": "uploading",
        }

    try:
        return await run_with_page(_run, headless=True)
    except Exception as e:
        logging.error("Failed to upload episode: %s", e)
        return {
            "title": episode_title,
            "season": season_number,
            "episode": episode_number,
            "status": "error",
            "message": str(e),
        }
    

async def upload_subtitle(
        subtitle_path: str = "",
        media_title: str = "",
        language: str = "",
        season_number: str = "",
        episode_number: str = "",
) -> dict:
    """Upload a subtitle file to the website."""

    async def _run(page: Page) -> dict:
        await page.goto(REDPANDA_MEDIA_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
        await redpanda_login(page=page)
        await page.goto(REDPANDA_MEDIA_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        logging.info(f"Uploading subtitle from path: {subtitle_path}")

        if not subtitle_path:
            raise ValueError("Subtitle path is required.")
        
        await page.get_by_role("link", name=re.compile(media_title, re.IGNORECASE)).click()
        
        # If it's an episode, navigate to the episode page first.
        if season_number.strip() and episode_number.strip():
            await page.select_option('#seasonSelect', season_number)
            episode_link = page.locator(
                "a.btn.btn-dark.w-100",
                has_text=f"Episode {episode_number}",
            ).first
            await episode_link.click()
            await page.wait_for_load_state("networkidle")
        
        add_atribute_url = page.url.replace("/media/", "/add-attribute/")
        await page.goto(add_atribute_url, wait_until="domcontentloaded")

        if language:
            await page.get_by_label("Language").select_option(label=language.title())

        await page.get_by_role("button", name="File").set_input_files(vtt_subtitle_path)

        await page.get_by_role("button", name="Add Attribute").click()

        return {
            "subtitle_path": vtt_subtitle_path,
            "status": "uploaded",
        }
    
    vtt_subtitle_path = re.sub(r"\.\w+$", ".vtt", subtitle_path)

    try:
        logging.info(f"Processing subtitle file: {subtitle_path} to VTT format at: {vtt_subtitle_path}")
        process_subtitles(subtitle_path, vtt_subtitle_path)
        logging.info(f"Subtitle file processed successfully, starting upload.")
        return await run_with_page(_run, headless=True)
    except Exception as e:
        logging.error("Failed to upload subtitle: %s", e)
        return {
            "subtitle_path": vtt_subtitle_path,
            "status": "error",
            "message": str(e),
        }
