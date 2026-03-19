import asyncio
from typing import Awaitable, Callable, TypeVar
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright



playwright: Playwright | None = None
browser: Browser | None = None
context: BrowserContext | None = None
page: Page | None = None
active_locale: str | None = None
active_timezone_id: str | None = None
_browser_lock = asyncio.Lock()

T = TypeVar("T")


async def _ensure_browser_unlocked(
    headless: bool = True,
    locale: str = "en-US",
    timezone_id: str | None = None,
) -> Page:
    global playwright, browser, context, page, active_locale, active_timezone_id

    needs_new_page = browser is None or page is None or page.is_closed()
    config_changed = locale != active_locale or timezone_id != active_timezone_id

    if browser is not None and config_changed:
        await _close_browser_unlocked()
        needs_new_page = True

    if needs_new_page:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)
        context_kwargs = {"locale": locale}
        if timezone_id:
            context_kwargs["timezone_id"] = timezone_id
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()
        active_locale = locale
        active_timezone_id = timezone_id

    return page


async def start_browser(
    headless: bool = True,
    locale: str = "en-US",
    timezone_id: str | None = None,
) -> Page:
    """Start the browser if it is not already running."""
    async with _browser_lock:
        return await _ensure_browser_unlocked(
            headless=headless,
            locale=locale,
            timezone_id=timezone_id,
        )


async def get_page() -> Page | None:
    """Return the active page instance."""
    async with _browser_lock:
        return page


async def run_with_page(
    callback: Callable[[Page], Awaitable[T]],
    *,
    headless: bool = True,
    locale: str = "en-US",
    timezone_id: str | None = None,
) -> T:
    """Run browser actions under a single lock using a persistent page/context."""
    async with _browser_lock:
        active_page = await _ensure_browser_unlocked(
            headless=headless,
            locale=locale,
            timezone_id=timezone_id,
        )
        return await callback(active_page)


async def _close_browser_unlocked() -> None:
    global browser, context, page, playwright, active_locale, active_timezone_id

    if page and not page.is_closed():
        await page.close()
    if context:
        await context.close()
    if browser:
        await browser.close()
    if playwright:
        await playwright.stop()

    browser = None
    context = None
    page = None
    playwright = None
    active_locale = None
    active_timezone_id = None


async def close_browser() -> None:
    """Close browser and cleanup."""
    async with _browser_lock:
        await _close_browser_unlocked()
