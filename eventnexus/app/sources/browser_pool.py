"""Shared Playwright browser pool for web scrapers.

Runs Playwright in a dedicated long-lived thread to avoid conflicts with
FastAPI's asyncio event loop (Playwright sync API cannot run
inside an asyncio loop).
"""

import logging
import queue
import threading

logger = logging.getLogger(__name__)

_request_queue: queue.Queue = queue.Queue()
_worker_thread: threading.Thread | None = None
_lock = threading.Lock()


def _worker_loop():
    """Long-lived worker that owns the Playwright browser."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    logger.info("Playwright browser launched in worker thread")

    while True:
        item = _request_queue.get()
        if item is None:  # shutdown signal
            break
        url, timeout_ms, wait_ms, result_q = item
        try:
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
                html = page.content()
                result_q.put(("ok", html))
            finally:
                page.close()
                context.close()
        except Exception as e:
            result_q.put(("error", e))

    browser.close()
    pw.stop()


def _ensure_worker():
    """Start the worker thread if not already running."""
    global _worker_thread
    with _lock:
        if _worker_thread is None or not _worker_thread.is_alive():
            _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
            _worker_thread.start()


def scrape_page(url: str, timeout_ms: int = 30000, wait_ms: int = 3000) -> str:
    """Navigate to URL and return the rendered HTML.

    Sends the request to the dedicated Playwright worker thread.
    """
    _ensure_worker()
    result_q: queue.Queue = queue.Queue()
    _request_queue.put((url, timeout_ms, wait_ms, result_q))

    try:
        status, value = result_q.get(timeout=90)
    except queue.Empty:
        raise TimeoutError(f"Scrape timed out for {url}")

    if status == "error":
        raise value
    return value


def close_browser() -> None:
    """Shut down the worker thread."""
    global _worker_thread
    with _lock:
        if _worker_thread and _worker_thread.is_alive():
            _request_queue.put(None)
            _worker_thread.join(timeout=10)
            _worker_thread = None
