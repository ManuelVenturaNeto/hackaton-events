"""Shared Playwright browser pool for web scrapers.

Manages a single Chromium browser instance reused across all scraper sources.
Uses sync Playwright API (not async) to match the existing ThreadPoolExecutor pattern.
"""

import logging
from playwright.sync_api import sync_playwright, Browser, Page

logger = logging.getLogger(__name__)

_playwright = None
_browser = None


def get_browser() -> Browser:
    """Get or create the shared Playwright browser instance."""
    global _playwright, _browser
    if _browser is None or not _browser.is_connected():
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("Playwright browser launched")
    return _browser


def new_page() -> Page:
    """Create a new browser page with standard settings."""
    browser = get_browser()
    context = browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        locale="pt-BR",
        viewport={"width": 1280, "height": 720},
    )
    return context.new_page()


def close_browser() -> None:
    """Close the shared browser instance."""
    global _playwright, _browser
    if _browser:
        _browser.close()
        _browser = None
    if _playwright:
        _playwright.stop()
        _playwright = None
