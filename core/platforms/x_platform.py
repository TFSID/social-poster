import asyncio
from typing import Dict, Any, Optional, Tuple
from core.platforms.base import BasePlatform

class XPlatform(BasePlatform):
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        super().__init__(options)
        self.platform_name = "x"
        self.base_url = "https://x.com"

    async def login_interactive_browserless(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not self.service: return None, None, None

        session = await self.service.create_session()
        if not session: return None, None, None

        # We need to navigate to X first?
        # But we can't easily navigate via CDP without writing complex code.
        # User can type URL in the Live Browser.
        # OR we can inject a goto via /function targeting the session? No, /function makes new session.
        # We can use CDP "Page.navigate" via websockets!

        # Let's add a quick navigate helper in BrowserlessService later if needed,
        # but for now, Live Browser starts at about:blank. User types url?
        # Better: Use Runtime.evaluate to window.location = ...

        # NOTE: For simplicity, we assume user can navigate or we add a helper.
        # Let's just return the session details. The Live URL usually has an address bar.

        return session.get("live_url"), session.get("id"), session.get("ws_url")

    async def check_login_status(self, ws_url: str) -> bool:
        if not self.service: return False
        # X login check selector
        return await self.service.check_selector(ws_url, '[data-testid="SideNav_AccountSwitcher_Button"]')

    async def post(self, content: Dict[str, Any], cookies: list) -> Dict[str, Any]:
        if not self.service: return {"success": False, "error": "No Browserless Token"}

        text = content.get("text", "")
        link = content.get("link", "")
        full_text = f"{text} {link}".strip()

        # Puppeteer script for X
        code = f"""
        module.exports = async ({{ page }}) => {{
            await page.goto('https://x.com');
            try {{
                await page.waitForSelector('[data-testid="SideNav_NewTweet_Button"]', {{timeout: 10000}});
                await page.click('[data-testid="SideNav_NewTweet_Button"]');
                await page.waitForSelector('[data-testid="tweetTextarea_0"]');
                await page.type('[data-testid="tweetTextarea_0"]', {repr(full_text)});
                await page.click('[data-testid="tweetButtonInline"]');
                await page.waitForResponse(response => response.url().includes('/create.json') && response.status() === 200);
                return {{ url: page.url() }};
            }} catch (e) {{
                throw e;
            }}
        }};
        """

        context = {"cookies": cookies}
        return await self.service.run_function(code, context)
