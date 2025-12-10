import os
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright

from core.session_manager import SessionManager

class BrowserAutomation:
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options = options or {}
        self.headless = self.options.get("headless", True)
        self.timeout = self.options.get("timeout", 30000)
        self.viewport = self.options.get("viewport", {"width": 1920, "height": 1080})
        self.user_agent = self.options.get("userAgent", 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        self.session_manager = SessionManager(self.options.get("sessionsPath"))
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None

    async def launch_browser(self) -> Browser:
        """Launch Playwright browser."""
        if self.browser:
            return self.browser

        if not self.playwright:
            self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
            ]
        )
        return self.browser

    async def close_browser(self):
        """Close browser and playwright."""
        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def create_page(self, platform: str) -> Page:
        """Create a new page with session restoration."""
        browser = await self.launch_browser()

        # Create context with viewport and user agent
        context = await browser.new_context(
            viewport=self.viewport,
            user_agent=self.user_agent
        )

        # Restore session if available
        session = self.session_manager.get_session(platform)
        if session and self.session_manager.is_session_valid(platform):
            await self.restore_session(context, session)

        page = await context.new_page()
        return page

    async def restore_session(self, context: BrowserContext, session: Dict[str, Any]):
        """Restore session data to context."""
        try:
            # Set cookies
            cookies = session.get("cookies", [])
            if cookies:
                await context.add_cookies(cookies)

            # LocalStorage/SessionStorage restoration is tricky in Playwright because
            # it needs to be done *after* opening the page for a specific origin.
            # We will handle that in the platform-specific implementation or
            # by navigating to the base URL first if needed.
        except Exception as e:
            print(f"Failed to restore session: {e}")

    async def capture_session(self, page: Page) -> Dict[str, Any]:
        """Capture session data from page."""
        try:
            context = page.context
            cookies = await context.cookies()

            # Get user agent
            user_agent = await page.evaluate("() => navigator.userAgent")

            # Get storage
            # Note: This only gets storage for the current origin of the page
            local_storage = await page.evaluate("""() => {
                const storage = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    storage[key] = localStorage.getItem(key);
                }
                return storage;
            }""")

            session_storage = await page.evaluate("""() => {
                const storage = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    storage[key] = sessionStorage.getItem(key);
                }
                return storage;
            }""")

            session = {
                "lastValidated": datetime.now().astimezone().isoformat(),
                "userAgent": user_agent,
                "viewport": self.viewport,
                "cookies": cookies,
                "localStorage": local_storage,
                "sessionStorage": session_storage
            }
            return session
        except Exception as e:
            print(f"Failed to capture session: {e}")
            return {
                "lastValidated": datetime.now().astimezone().isoformat(),
                "cookies": []
            }

    async def save_session(self, page: Page, platform: str):
        """Save current page session for platform."""
        session = await self.capture_session(page)
        self.session_manager.set_session(platform, session)

    # --- Helper methods ---

    async def wait_for_element(self, page: Page, selector: str, timeout: Optional[int] = None):
        if timeout is None:
            timeout = self.timeout
        return await page.wait_for_selector(selector, timeout=timeout)

    async def type_text(self, page: Page, selector: str, text: str, delay: int = 50):
        element = await self.wait_for_element(page, selector)
        await element.click(click_count=3) # Select all
        await element.press("Backspace")
        await element.type(text, delay=delay)

    async def click_element(self, page: Page, selector: str, delay: bool = True):
        element = await self.wait_for_element(page, selector)
        if delay:
            await page.wait_for_timeout(500)
        await element.click()
