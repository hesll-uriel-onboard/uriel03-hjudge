"""Browser automation utilities for judges that require it."""

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Generator

from playwright.async_api import async_playwright, Browser, Page, Playwright


class BrowserCrawler(ABC):
    """Base class for browser-based crawling using Playwright.

    This class handles browser lifecycle and provides utilities for
    crawling pages that require JavaScript or bypass Cloudflare.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )

    async def close(self):
        """Close the browser and playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    @asynccontextmanager
    async def new_page(self) -> Generator[Page, None, None]:
        """Create a new page context."""
        await self._ensure_browser()
        page = await self._browser.new_page()
        try:
            yield page
        finally:
            await page.close()

    async def wait_for_cloudflare(self, page: Page, timeout: int = 30000):
        """Wait for Cloudflare challenge to complete.

        Args:
            page: The Playwright page
            timeout: Maximum time to wait in milliseconds
        """
        # Wait for Cloudflare challenge to pass
        # Cloudflare typically shows a challenge page that auto-submits
        try:
            # Check if we're on a Cloudflare challenge page
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass  # Continue even if timeout

    async def get_page_content(self, url: str, wait_for: str | None = None) -> str:
        """Navigate to URL and get page content.

        Args:
            url: The URL to navigate to
            wait_for: Optional selector to wait for before extracting content

        Returns:
            The page HTML content
        """
        async with self.new_page() as page:
            await page.goto(url)

            # Wait for Cloudflare if present
            await self.wait_for_cloudflare(page)

            # Wait for specific selector if provided
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=30000)

            return await page.content()


class SyncBrowserCrawler:
    """Synchronous wrapper for BrowserCrawler.

    Playwright is async-only, so this wrapper runs the async methods
    in an event loop. This allows synchronous code to use browser crawling.
    """

    def __init__(self, headless: bool = True):
        self._crawler = BrowserCrawler(headless=headless)
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def get_page_content(self, url: str, wait_for: str | None = None) -> str:
        """Synchronously get page content.

        Args:
            url: The URL to navigate to
            wait_for: Optional selector to wait for

        Returns:
            The page HTML content
        """
        loop = self._get_loop()
        return loop.run_until_complete(
            self._crawler.get_page_content(url, wait_for)
        )

    def close(self):
        """Close the browser."""
        loop = self._get_loop()
        loop.run_until_complete(self._crawler.close())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False