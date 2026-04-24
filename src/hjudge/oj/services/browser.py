"""Browser automation utilities for judges that require it."""

import asyncio
import os
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
FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL", "http://localhost:8191/v1")

# Credentials from environment
QOJ_USERNAME = os.getenv("QOJ_USERNAME", "")
QOJ_PASSWORD = os.getenv("QOJ_PASSWORD", "")
ATCODER_USERNAME = os.getenv("ATCODER_USERNAME", "")
ATCODER_PASSWORD = os.getenv("ATCODER_PASSWORD", "")

# Cookie files for manual login bypass
QOJ_COOKIE_FILE = os.getenv("QOJ_COOKIE_FILE", "")
ATCODER_COOKIE_FILE = os.getenv("ATCODER_COOKIE_FILE", "")


class FlareSolverrCrawler:
    """Cloudflare bypass using FlareSolverr service.

    FlareSolverr is a proxy server that bypasses Cloudflare and DDoS-GUARD protection.
    Run it with: docker run -p 8191:8191 -e LOG_LEVEL=info ghcr.io/flaresolverr/flaresolverr:latest
    """

    def __init__(self, flaresolverr_url: str = FLARESOLVERR_URL, timeout: int = 60000):
        self.flaresolverr_url = flaresolverr_url
        self.timeout = timeout
        self._session: str | None = None
        self._logged_in_sites: set[str] = set()

    async def __aenter__(self) -> Self:
        # Create a browser session for reusing cookies across requests
        async with httpx.AsyncClient(timeout=self.timeout / 1000) as client:
            response = await client.post(
                self.flaresolverr_url,
                json={
                    "cmd": "sessions.create",
                    "session": "hjudge_session",
                },
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self._session = "hjudge_session"
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # Destroy the session when done
        if self._session:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        self.flaresolverr_url,
                        json={
                            "cmd": "sessions.destroy",
                            "session": self._session,
                        },
                    )
            except Exception:
                pass
        return None

    async def _login_atcoder(self) -> bool:
        """Login to AtCoder using credentials."""
        if not ATCODER_USERNAME or not ATCODER_PASSWORD:
            return False

        if "atcoder" in self._logged_in_sites:
            return True

        try:
            # First, get the login page to get CSRF token
            async with httpx.AsyncClient(timeout=self.timeout / 1000) as client:
                response = await client.post(
                    self.flaresolverr_url,
                    json={
                        "cmd": "request.get",
                        "url": "https://atcoder.jp/login",
                        "session": self._session,
                        "maxTimeout": self.timeout,
                    },
                )

                if response.status_code != 200:
                    return False

                data = response.json()
                if data.get("status") != "ok":
                    return False

                html = data["solution"]["response"]

                # Extract CSRF token
                from bs4 import BeautifulSoup
                import re

                soup = BeautifulSoup(html, "html.parser")
                csrf_input = soup.find("input", {"name": "csrf_token"})
                csrf_token = csrf_input.get("value") if csrf_input else ""

                if not csrf_token:
                    # Try to find in meta tag
                    csrf_meta = soup.find("meta", {"name": "csrf-token"})
                    if csrf_meta:
                        csrf_token = csrf_meta.get("content", "")

                # Also extract from script
                if not csrf_token:
                    match = re.search(r'csrfToken\s*=\s*["\']([^"\']+)["\']', html)
                    if match:
                        csrf_token = match.group(1)

                # Login via POST
                login_response = await client.post(
                    self.flaresolverr_url,
                    json={
                        "cmd": "request.post",
                        "url": "https://atcoder.jp/login",
                        "session": self._session,
                        "postData": f"username={ATCODER_USERNAME}&password={ATCODER_PASSWORD}&csrf_token={csrf_token}",
                        "maxTimeout": self.timeout,
                    },
                )

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    if login_data.get("status") == "ok":
                        self._logged_in_sites.add("atcoder")
                        return True

        except Exception:
            pass

        return False

    async def _login_qoj(self) -> bool:
        """Login to QOJ using credentials."""
        if not QOJ_USERNAME or not QOJ_PASSWORD:
            return False

        if "qoj" in self._logged_in_sites:
            return True

        try:
            import hashlib
            import re

            async with httpx.AsyncClient(timeout=self.timeout / 1000) as client:
                # Get login page to extract the per-request _token from inline JS
                response = await client.post(
                    self.flaresolverr_url,
                    json={
                        "cmd": "request.get",
                        "url": "https://qoj.ac/login",
                        "session": self._session,
                        "maxTimeout": self.timeout,
                    },
                )

                if response.status_code != 200:
                    return False

                data = response.json()
                if data.get("status") != "ok":
                    return False

                html = data["solution"]["response"]

                # QOJ embeds the _token in an inline script (not a form input)
                match = re.search(r"_token\s*:\s*[\"']([^\"']+)[\"']", html)
                token = match.group(1) if match else ""

                # QOJ AJAX login: password is MD5-hashed client-side
                md5_password = hashlib.md5(QOJ_PASSWORD.encode()).hexdigest()
                post_data = f"_token={token}&login=&username={QOJ_USERNAME}&password={md5_password}"

                login_response = await client.post(
                    self.flaresolverr_url,
                    json={
                        "cmd": "request.post",
                        "url": "https://qoj.ac/login",
                        "session": self._session,
                        "postData": post_data,
                        "maxTimeout": self.timeout,
                    },
                )

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    if login_data.get("status") == "ok":
                        from bs4 import BeautifulSoup
                        raw = login_data.get("solution", {}).get("response", "")
                        body_text = BeautifulSoup(raw, "html.parser").get_text(strip=True)
                        if body_text == "ok":
                            self._logged_in_sites.add("qoj")
                            return True

        except Exception:
            pass

        return False

    async def get_page_content(self, url: str, wait_for: str | None = None, skip_login: bool = False) -> str:
        """Get page content via FlareSolverr.

        Args:
            url: The URL to navigate to
            wait_for: Optional CSS selector to wait for (uses browser commands)
            skip_login: If True, skip login attempts (useful for public pages)

        Returns:
            The page HTML content
        """
        # Login if needed and not skipped
        if not skip_login:
            if "atcoder.jp" in url:
                await self._login_atcoder()
            elif "qoj.ac" in url:
                await self._login_qoj()

        request_data = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": self.timeout,
        }

        # Use session if available for cookie persistence
        if self._session:
            request_data["session"] = self._session

        async with httpx.AsyncClient(timeout=self.timeout / 1000) as client:
            response = await client.post(
                self.flaresolverr_url,
                json=request_data,
            )

            if response.status_code != 200:
                raise RuntimeError(f"FlareSolverr failed: {response.status_code} - {response.text}")

            data = response.json()
            if data.get("status") != "ok":
                raise RuntimeError(f"FlareSolverr error: {data.get('message', 'Unknown error')}")

            html_content = data["solution"]["response"]

            # If wait_for is specified, check if element exists
            # FlareSolverr doesn't support wait_for directly, but we can verify
            if wait_for:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, "html.parser")
                element = soup.select_one(wait_for)
                if element is None:
                    # Element not found - could be still loading or doesn't exist
                    # Just return what we have
                    pass

            return html_content


class AsyncBrowserCrawler:
    """Async browser crawler using Playwright with persistent browser lifecycle.

    This class is an async context manager that initializes a browser tab ONCE
    and keeps it alive for reuse across multiple requests. The tab only closes
    when the context manager exits.

    Includes Cloudflare bypass via playwright-stealth and login support.

    Usage:
        async with AsyncBrowserCrawler(headless=True) as crawler:
            content1 = await crawler.get_page_content(url1)
            content2 = await crawler.get_page_content(url2)  # Same tab reused
    """

    def __init__(self, headless: bool = True, bypass_cloudflare: bool = True):
        self.headless = headless
        self.bypass_cloudflare = bypass_cloudflare
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._logged_in_sites: set[str] = set()

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

        # Create context with more realistic settings
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": random.choice(USER_AGENTS),
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }

        self._context = await self._browser.new_context(**context_options)

        # Bootstrap Cloudflare clearance cookies via FlareSolverr
        if self.bypass_cloudflare:
            await self._bootstrap_cf_cookies()

        # Load cookies if available
        self._load_cookies()

        self._page = await self._context.new_page()

        # Apply stealth if bypassing Cloudflare
        if self.bypass_cloudflare:
            stealth = Stealth(navigator_webdriver=True)
            await stealth.apply_stealth_async(self._page)

        return self

    async def _bootstrap_cf_cookies(self) -> None:
        """Fetch Cloudflare clearance cookies from FlareSolverr and inject into Playwright context."""
        urls = ["https://qoj.ac/", "https://atcoder.jp/"]
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                await client.post(FLARESOLVERR_URL, json={"cmd": "sessions.create", "session": "cf_bootstrap"})
                for url in urls:
                    try:
                        r = await client.post(FLARESOLVERR_URL, json={
                            "cmd": "request.get",
                            "url": url,
                            "session": "cf_bootstrap",
                            "maxTimeout": 60000,
                        })
                        data = r.json()
                        if data.get("status") != "ok":
                            continue
                        raw_cookies = data.get("solution", {}).get("cookies", [])
                        playwright_cookies = [
                            {
                                "name": c["name"],
                                "value": c["value"],
                                "domain": c["domain"],
                                "path": c.get("path", "/"),
                                "httpOnly": c.get("httpOnly", False),
                                "secure": c.get("secure", False),
                            }
                            for c in raw_cookies
                        ]
                        if playwright_cookies:
                            await self._context.add_cookies(playwright_cookies)
                    except Exception:
                        pass
                await client.post(FLARESOLVERR_URL, json={"cmd": "sessions.destroy", "session": "cf_bootstrap"})
        except Exception:
            pass

    def _load_cookies(self) -> None:
        """Load cookies from file into browser context."""
        import json

        # Load QOJ cookies
        if QOJ_COOKIE_FILE and os.path.exists(QOJ_COOKIE_FILE):
            try:
                with open(QOJ_COOKIE_FILE, "r") as f:
                    cookies = json.load(f)
                    self._context.add_cookies(cookies)
                    self._logged_in_sites.add("qoj")
            except Exception:
                pass

        # Load AtCoder cookies
        if ATCODER_COOKIE_FILE and os.path.exists(ATCODER_COOKIE_FILE):
            try:
                with open(ATCODER_COOKIE_FILE, "r") as f:
                    cookies = json.load(f)
                    self._context.add_cookies(cookies)
                    self._logged_in_sites.add("atcoder")
            except Exception:
                pass

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close browser and playwright."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        return None

    async def _login_atcoder(self) -> bool:
        """Login to AtCoder using credentials."""
        if not ATCODER_USERNAME or not ATCODER_PASSWORD:
            return False

        if "atcoder" in self._logged_in_sites:
            return True

        try:
            # Navigate to login page
            await self._page.goto("https://atcoder.jp/login", wait_until="domcontentloaded")
            await self._page.wait_for_load_state("networkidle", timeout=30000)

            # Wait for Cloudflare challenge if present
            await asyncio.sleep(2)
            await self._page.wait_for_load_state("networkidle", timeout=15000)

            # Check if already logged in (redirected to home)
            if self._page.url == "https://atcoder.jp/" or "/login" not in self._page.url:
                self._logged_in_sites.add("atcoder")
                return True

            # Fill in login form
            await self._page.fill("input[name='username']", ATCODER_USERNAME)
            await self._page.fill("input[name='password']", ATCODER_PASSWORD)

            # Click login button
            await self._page.click("button[type='submit']")

            # Wait for response
            await self._page.wait_for_load_state("networkidle", timeout=30000)

            # Check if login successful (redirected away from login page)
            if "/login" not in self._page.url:
                self._logged_in_sites.add("atcoder")
                return True

            return False

        except Exception:
            return False

    async def _login_qoj(self) -> bool:
        """Login to QOJ using credentials."""
        if not QOJ_USERNAME or not QOJ_PASSWORD:
            return False

        if "qoj" in self._logged_in_sites:
            return True

        try:
            # Navigate to login page
            await self._page.goto("https://qoj.ac/login", wait_until="domcontentloaded")
            await self._page.wait_for_load_state("networkidle", timeout=30000)

            # Wait for Cloudflare challenge if present
            await asyncio.sleep(2)
            await self._page.wait_for_load_state("networkidle", timeout=15000)

            # Check if already logged in
            if "/login" not in self._page.url:
                self._logged_in_sites.add("qoj")
                return True

            # Fill in login form
            await self._page.fill("input[name='username']", QOJ_USERNAME)
            await self._page.fill("input[name='password']", QOJ_PASSWORD)

            # Click login button
            await self._page.click("button[type='submit'], input[type='submit']")

            # Wait for response
            await self._page.wait_for_load_state("networkidle", timeout=30000)

            # Check if login successful
            if "/login" not in self._page.url:
                self._logged_in_sites.add("qoj")
                return True

            return False

        except Exception:
            return False

    async def get_page_content(self, url: str, wait_for: str | None = None, skip_login: bool = False) -> str:
        """Navigate to URL and get page content using the persistent page.

        Args:
            url: The URL to navigate to
            wait_for: Optional selector to wait for before extracting content
            skip_login: If True, skip login attempts (useful for public pages)

        Returns:
            The page HTML content
        """
        if self._page is None:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        # Login if needed and not skipped
        if not skip_login:
            if "atcoder.jp" in url:
                await self._login_atcoder()
            elif "qoj.ac" in url:
                await self._login_qoj()

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
            try:
                await self._page.wait_for_selector(wait_for, timeout=30000)
            except Exception:
                pass

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


def export_cookies_help():
    """Print instructions for exporting cookies from browser.

    Cookies need to be exported in JSON format as a list of cookie objects.
    Each cookie object should have: name, value, domain, path (optional).

    For Chrome/Edge:
    1. Install "EditThisCookie" extension
    2. Login to the site (AtCoder/QOJ)
    3. Click the extension icon
    4. Click "Export" to get JSON
    5. Save to a file (e.g., .creds/atcoder_cookies.json)

    For Firefox:
    1. Install "Cookie Quick Manager" extension
    2. Login to the site
    3. Export cookies for the domain
    4. Save to a file

    Cookie format example:
    [
        {
            "name": "REMEMBERME",
            "value": "some_value",
            "domain": "atcoder.jp",
            "path": "/"
        }
    ]

    Set environment variables:
    - ATCODER_COOKIE_FILE=/path/to/atcoder_cookies.json
    - QOJ_COOKIE_FILE=/path/to/qoj_cookies.json
    """
    print(export_cookies_help.__doc__)