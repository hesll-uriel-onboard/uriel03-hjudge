"""Browser automation utilities for judges that require it."""

import asyncio
import random
from typing import Self

import httpx
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from playwright_stealth import Stealth


# Common user agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Default FlareSolverr URL
FLARESOLVERR_URL = "http://localhost:8191/v1"


class FlareSolverrCrawler:
    """Cloudflare bypass using FlareSolverr service.

    FlareSolverr is a proxy server that bypasses Cloudflare and DDoS-GUARD protection.
    Run it with: docker run -p 8191:8191 -e LOG_LEVEL=info ghcr.io/flaresolverr/flaresolverr:latest
    """

    def __init__(self, flaresolverr_url: str = FLARESOLVERR_URL, timeout: int = 60000):
        self.flaresolverr_url = flaresolverr_url
        self.timeout = timeout

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    async def get_page_content(self, url: str, wait_for: str | None = None) -> str:
        """Get page content via FlareSolverr.

        Args:
            url: The URL to navigate to
            wait_for: Ignored (FlareSolverr handles waiting)

        Returns:
            The page HTML content
        """
        async with httpx.AsyncClient(timeout=self.timeout / 1000) as client:
            response = await client.post(
                self.flaresolverr_url,
                json={
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": self.timeout,
                },
            )

            if response.status_code != 200:
                raise RuntimeError(f"FlareSolverr failed: {response.status_code} - {response.text}")

            data = response.json()
            if data.get("status") != "ok":
                raise RuntimeError(f"FlareSolverr error: {data.get('message', 'Unknown error')}")

            return data["solution"]["response"]


class AsyncBrowserCrawler:
    """Async browser crawler using Playwright with persistent browser lifecycle.

    This class is an async context manager that initializes a browser tab ONCE
    and keeps it alive for reuse across multiple requests. The tab only closes
    when the context manager exits.

    Includes Cloudflare bypass via playwright-stealth.

    Usage:
        async with AsyncBrowserCrawler(headless=True) as crawler:
            content1 = await crawler.get_page_content(url1)
            content2 = await crawler.get_page_content(url2)  # Same tab reused
    """

    def __init__(self, headless: bool = True, bypass_cloudflare: bool = False):
        self.headless = headless
        self.bypass_cloudflare = bypass_cloudflare
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> Self:
        """Initialize playwright, browser, and page ONCE."""
        self._playwright = await async_playwright().start()

        # Launch options
        launch_options = {
            "headless": self.headless,
        }

        if self.bypass_cloudflare:
            launch_options["args"] = [
                "--disable-blink-features=AutomationControlled",
            ]

        self._browser = await self._playwright.chromium.launch(**launch_options)

        # Create context
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": random.choice(USER_AGENTS),
        }

        self._context = await self._browser.new_context(**context_options)
        self._page = await self._context.new_page()

        # Apply stealth if bypassing Cloudflare
        if self.bypass_cloudflare:
            stealth = Stealth(navigator_webdriver=True)
            await stealth.apply_stealth_async(self._page)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close browser and playwright."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        return None

    async def get_page_content(self, url: str, wait_for: str | None = None) -> str:
        """Navigate to URL and get page content using the persistent page.

        Args:
            url: The URL to navigate to
            wait_for: Optional selector to wait for before extracting content

        Returns:
            The page HTML content
        """
        if self._page is None:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        await self._page.goto(url, wait_until="domcontentloaded")

        # Wait for Cloudflare/network idle
        try:
            await self._page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass

        # Additional wait for Cloudflare challenge if bypass mode
        if self.bypass_cloudflare:
            try:
                await asyncio.sleep(2)
                await self._page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

        # Wait for specific selector if provided
        if wait_for:
            await self._page.wait_for_selector(wait_for, timeout=30000)

        return await self._page.content()


class SyncBrowserCrawler:
    """Synchronous wrapper for browser crawling using subprocess isolation.

    DEPRECATED: Use AsyncBrowserCrawler instead for persistent browser lifecycle.
    This class is kept for backwards compatibility but creates a fresh browser
    for each request.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    def get_page_content(self, url: str, wait_for: str | None = None) -> str:
        """Synchronously get page content via subprocess.

        Args:
            url: The URL to navigate to
            wait_for: Optional selector to wait for

        Returns:
            The page HTML content
        """
        import subprocess
        import sys
        import json

        script = '''
import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def main():
    args = json.loads(sys.argv[1])
    url = args["url"]
    wait_for = args.get("wait_for")
    headless = args.get("headless", True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        await page.goto(url)
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
        except:
            pass
        if wait_for:
            await page.wait_for_selector(wait_for, timeout=30000)
        content = await page.content()
        await browser.close()
        print(content, end="")

asyncio.run(main())
'''
        args = json.dumps({
            "url": url,
            "wait_for": wait_for,
            "headless": self.headless
        })

        result = subprocess.run(
            [sys.executable, "-c", script, args],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            raise RuntimeError(f"Browser subprocess failed: {result.stderr}")

        return result.stdout

    def close(self):
        """Close (no-op for subprocess mode)."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False