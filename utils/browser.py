from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright



# Global browser and page objects
playwright: Playwright | None = None
browser: Browser | None = None
context: BrowserContext | None = None
page: Page | None = None
active_locale: str | None = None
active_timezone_id: str | None = None


def start_browser(
    headless: bool = True,
    locale: str = "en-US",
    timezone_id: str | None = None,
) -> Page:
    """Start the browser if it is not already running.

    Locale defaults to English so websites like TMDB render predictable labels.
    """
    global playwright, browser, context, page, active_locale, active_timezone_id

    needs_new_page = browser is None or page is None or page.is_closed()
    config_changed = locale != active_locale or timezone_id != active_timezone_id

    if browser is not None and config_changed:
        close_browser()

    if needs_new_page or config_changed:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=headless)
        context_kwargs = {"locale": locale}
        if timezone_id:
            context_kwargs["timezone_id"] = timezone_id
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        active_locale = locale
        active_timezone_id = timezone_id

    return page


def get_page() -> Page | None:
    """Return the active page instance."""
    return page


def close_browser():
    """Close browser and cleanup."""
    global browser, context, page, playwright, active_locale, active_timezone_id

    if browser:
        if page and not page.is_closed():
            page.close()
        if context:
            context.close()
        browser.close()
        browser = None
        context = None
        page = None
        active_locale = None
        active_timezone_id = None

    if playwright:
        playwright.stop()
        playwright = None
