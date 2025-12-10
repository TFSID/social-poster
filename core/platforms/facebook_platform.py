import asyncio
from typing import Dict, Any, Optional
from core.platforms.base import BasePlatform

class FacebookPlatform(BasePlatform):
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        super().__init__(options)
        self.platform_name = "facebook"
        self.base_url = "https://www.facebook.com"
        self.login_url = "https://www.facebook.com/login"

    async def is_logged_in(self, page) -> bool:
        """Check if user is logged in to Facebook."""
        try:
            current_url = page.url
            if "/login" in current_url:
                return False

            try:
                await page.wait_for_selector('div[role="banner"]', timeout=3000)
                if await page.query_selector('div[role="feed"]'):
                    return True
                if await page.query_selector('[aria-label="Account controls and settings"]'):
                    return True
                return False
            except:
                return False
        except Exception as e:
            # print(f"Failed to check login status for Facebook: {e}")
            return False

    async def login(self, options: Optional[Dict[str, Any]] = None) -> bool:
        options = options or {}
        original_headless = self.headless
        if "headless" in options:
            self.headless = options["headless"]
            if self.browser:
                await self.close_browser()

        page = await self.create_page(self.platform_name)

        try:
            await page.goto(self.base_url, wait_until="networkidle")

            try:
                await page.click('[data-testid="cookie-policy-manage-dialog-accept-button"]', timeout=2000)
            except:
                pass

            if await self.is_logged_in(page):
                print("Already logged in to Facebook")
                await self.save_session(page, self.platform_name)
                return True

            if not self.headless:
                print("Please log in manually in the browser...")
                max_wait = 300
                start_time = asyncio.get_event_loop().time()

                while (asyncio.get_event_loop().time() - start_time) < max_wait:
                    if await self.is_logged_in(page):
                        print("Login detected!")
                        await self.save_session(page, self.platform_name)
                        return True
                    await asyncio.sleep(2)

                print("Login timed out.")
                return False
            else:
                print("Automated login not implemented for Facebook.")
                return False

        except Exception as e:
            print(f"Facebook login failed: {e}")
            return False
        finally:
            await page.close()
            self.headless = original_headless

    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Facebook."""
        page = await self.create_page(self.platform_name)
        try:
            await page.goto(self.base_url, wait_until="networkidle")

            if not await self.is_logged_in(page):
                return {"success": False, "error": "Authentication required"}

            try:
                create_post_trigger = await page.wait_for_selector('div[role="button"] span:has-text("What\'s on your mind")', timeout=5000)
                if not create_post_trigger:
                     create_post_trigger = await page.wait_for_selector('div[role="button"] span:has-text("What")', timeout=1000)

                await create_post_trigger.click()
            except Exception as e:
                return {"success": False, "error": f"Could not find 'Create Post' trigger: {e}"}

            try:
                modal = await page.wait_for_selector('div[role="dialog"][aria-label="Create post"]', timeout=5000)
                input_area = await modal.wait_for_selector('div[contenteditable="true"][role="textbox"]', timeout=2000)
            except Exception as e:
                 return {"success": False, "error": f"Could not find post modal/input: {e}"}

            text = content.get("text", "")
            link = content.get("link", "")
            full_text = f"{text}\n\n{link}".strip()

            await input_area.click()
            await page.keyboard.type(full_text)

            if link:
                await page.wait_for_timeout(3000)

            try:
                post_btn = await modal.wait_for_selector('div[aria-label="Post"]', timeout=2000)
                await post_btn.click()
            except Exception as e:
                return {"success": False, "error": f"Could not find or click 'Post' button: {e}"}

            try:
                await page.wait_for_selector('div[role="dialog"][aria-label="Create post"]', state="hidden", timeout=10000)
                return {
                    "success": True,
                    "platform": "facebook",
                    "timestamp": asyncio.get_event_loop().time()
                }
            except:
                return {"success": False, "error": "Post timeout - Modal did not close"}

        except Exception as e:
            return {"success": False, "error": str(e), "platform": "facebook"}
        finally:
            await page.close()
