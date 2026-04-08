"""Shared Playwright browser pool for web scrapers.

Runs Playwright in a dedicated thread to avoid conflicts with
FastAPI's asyncio event loop (Playwright sync API cannot run
inside an asyncio loop).
"""

import logging
import threading
from concurrent.futures import Future
from playwright.sync_api import sync_playwright, Browser, Page

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_playwright = None
_browser = None


def _ensure_browser() -> Browser:
    """Get or create the shared browser instance. Thread-safe."""
    global _playwright, _browser
    with _lock:
        if _browser is None or not _browser.is_connected():
            _playwright = sync_playwright().start()
            _browser = _playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            logger.info("Playwright browser launched")
        return _browser


def _run_in_thread(fn):
    """Run a function in a new thread to escape the asyncio event loop."""
    result_future: Future = Future()

    def wrapper():
        try:
            result_future.set_result(fn())
        except Exception as e:
            result_future.set_exception(e)

    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    t.join(timeout=60)
    return result_future.result(timeout=0)


def scrape_page(url: str, timeout_ms: int = 30000, wait_ms: int = 3000) -> str:
    """Navigate to URL and return the rendered HTML.

    Runs in a separate thread to avoid asyncio conflicts.
    Returns the full page HTML after JS rendering.
    """
    def _do_scrape() -> str:
        browser = _ensure_browser()
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="pt-BR",
            viewport={"width": 1280, "height": 720},
            extra_http_headers={"Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"},
        )
        page = context.new_page()
        try:
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            page.wait_for_timeout(wait_ms)
            return page.content()
        finally:
            page.close()
            context.close()

    return _run_in_thread(_do_scrape)


def close_browser() -> None:
    """Close the shared browser instance."""
    global _playwright, _browser
    with _lock:
        if _browser:
            _browser.close()
            _browser = None
        if _playwright:
            _playwright.stop()
            _playwright = None
