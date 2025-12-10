import os
import asyncio
import json
import requests
from datetime import datetime
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

        # Browserless Config
        self.browserless_token = self.options.get("browserless_token")
        self.use_browserless = self.options.get("use_browserless", False)
        self.browserless_session_id: Optional[str] = None

    async def launch_browser(self) -> Browser:
        """Launch Playwright browser (Local or Browserless)."""
        if self.browser:
            return self.browser

        if not self.playwright:
            self.playwright = await async_playwright().start()

        if self.use_browserless and self.browserless_token:
            print("🚀 Launching Browserless Session...")
            session_data = await self.create_browserless_session(self.browserless_token)
            if session_data:
                connect_url = session_data['connect']
                self.browserless_session_id = session_data['id']
                self.browser = await self.playwright.chromium.connect_over_cdp(connect_url)
                return self.browser
            else:
                print("⚠️ Failed to create Browserless session. Falling back to local.")

        # Local Launch
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

    async def create_browserless_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Create a Browserless session via REST API."""
        try:
            # Assumes SFO region
            url = f"https://production-sfo.browserless.io/session?token={token}"

            session_config = {
                "ttl": 300000, # 5 mins for interaction
                "stealth": True,
                "headless": False, # Important for interactive session? Or headless=False in args?
                                   # Session API 'headless' param controls if X11 is used?
                                   # Usually headless: false is needed for visual debugging.
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=session_config
            ))

            if not response.ok:
                print(f"Browserless HTTP error: {response.status_code} - {response.text}")
                return None

            session = response.json()
            print(f"Browserless Session Created: {session.get('id')}")
            return session
        except Exception as e:
            print(f"Error creating Browserless session: {e}")
            return None

    async def stop_browserless_session(self, session_id: str, token: str):
        """Stop a Browserless session."""
        if not session_id or not token:
            return

        try:
            url = f"https://production-sfo.browserless.io/session/{session_id}?token={token}&force=true"
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.delete(url))

            if response.ok:
                print(f"Browserless Session {session_id} stopped.")
            else:
                print(f"Failed to stop Browserless session: {response.status_code}")
        except Exception as e:
            print(f"Error stopping Browserless session: {e}")

    async def close_browser(self):
        """Close browser and playwright."""
        if self.browser:
            await self.browser.close()

            if self.use_browserless and self.browserless_session_id:
                await self.stop_browserless_session(self.browserless_session_id, self.browserless_token)
                self.browserless_session_id = None

            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def create_page(self, platform: str) -> Page:
        """Create a new page with session restoration."""
        browser = await self.launch_browser()

        # When using connect_over_cdp, we often attach to the existing target or create new context
        # Ideally, we create a new context to be safe
        context = await browser.new_context(
            viewport=self.viewport,
            user_agent=self.user_agent
        )

        session = self.session_manager.get_session(platform)
        if session and self.session_manager.is_session_valid(platform):
            await self.restore_session(context, session)

        page = await context.new_page()
        return page

    async def restore_session(self, context: BrowserContext, session: Dict[str, Any]):
        """Restore session data to context."""
        try:
            cookies = session.get("cookies", [])
            if cookies:
                await context.add_cookies(cookies)
        except Exception as e:
            print(f"Failed to restore session: {e}")

    async def capture_session(self, page: Page) -> Dict[str, Any]:
        """Capture session data from page."""
        try:
            context = page.context
            cookies = await context.cookies()
            user_agent = await page.evaluate("() => navigator.userAgent")

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
        await element.click(click_count=3)
        await element.press("Backspace")
        await element.type(text, delay=delay)

    async def click_element(self, page: Page, selector: str, delay: bool = True):
        element = await self.wait_for_element(page, selector)
        if delay:
            await page.wait_for_timeout(500)
        await element.click()
