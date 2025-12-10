import asyncio
from typing import Dict, Any, Optional, Tuple
from core.platforms.base import BasePlatform

class FacebookPlatform(BasePlatform):
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        super().__init__(options)
        self.platform_name = "facebook"
        self.base_url = "https://www.facebook.com"

    async def login_interactive_browserless(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not self.service: return None, None, None
        session = await self.service.create_session()
        if not session: return None, None, None
        return session.get("live_url"), session.get("id"), session.get("ws_url")

    async def check_login_status(self, ws_url: str) -> bool:
        if not self.service: return False
        # Facebook login check
        is_feed = await self.service.check_selector(ws_url, 'div[role="feed"]')
        is_account = await self.service.check_selector(ws_url, '[aria-label="Account controls and settings"]')
        return is_feed or is_account

    async def post(self, content: Dict[str, Any], cookies: list) -> Dict[str, Any]:
        if not self.service: return {"success": False, "error": "No Browserless Token"}

        text = content.get("text", "")
        link = content.get("link", "")
        full_text = f"{text}\\n\\n{link}".strip()

        # Puppeteer script for Facebook
        # Note: FB is complex. This is a best-effort script based on previous logic.
        code = f"""
        module.exports = async ({{ page }}) => {{
            await page.goto('https://facebook.com');
            try {{
                // Handle cookies if present
                try {{ await page.click('[data-testid="cookie-policy-manage-dialog-accept-button"]'); }} catch(e) {{}}

                await page.waitForSelector('div[role="feed"]', {{timeout: 10000}});

                // Click "What's on your mind"
                await page.evaluate(() => {{
                    const els = Array.from(document.querySelectorAll('div[role="button"] span'));
                    const target = els.find(el => el.textContent.includes("What's on your mind") || el.textContent.includes("What"));
                    if (target) target.click();
                    else throw new Error("Create post trigger not found");
                }});

                await page.waitForSelector('div[role="dialog"][aria-label="Create post"]');
                await page.waitForSelector('div[contenteditable="true"][role="textbox"]');

                await page.click('div[contenteditable="true"][role="textbox"]');
                await page.keyboard.type({repr(full_text)});

                await page.waitForTimeout(3000); // Wait for preview

                await page.click('div[aria-label="Post"]');

                // Wait for modal to disappear
                await page.waitForFunction(() => !document.querySelector('div[role="dialog"][aria-label="Create post"]'));

                return {{ success: true }};
            }} catch (e) {{
                throw e;
            }}
        }};
        """

        context = {"cookies": cookies}
        return await self.service.run_function(code, context)
