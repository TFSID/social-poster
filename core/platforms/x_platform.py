import asyncio
from typing import Dict, Any, Optional
from core.platforms.base import BasePlatform

class XPlatform(BasePlatform):
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        super().__init__(options)
        self.platform_name = "x"
        self.base_url = "https://x.com"
        self.login_url = "https://x.com/i/flow/login"
        self.max_text_length = 280

    async def is_logged_in(self, page) -> bool:
        """Check if user is logged in to X."""
        try:
            current_url = page.url
            if "/login" in current_url or "/i/flow/login" in current_url:
                return False

            try:
                await page.wait_for_selector('[data-testid="SideNav_AccountSwitcher_Button"]', timeout=3000)
                return True
            except:
                pass

            try:
                await page.wait_for_selector('[data-testid="AppTabBar_Profile_Link"]', timeout=1000)
                return True
            except:
                pass

            try:
                await page.wait_for_selector('[data-testid="primaryColumn"]', timeout=1000)
                return True
            except:
                pass

            return False
        except Exception as e:
            # print(f"Failed to check login status for X: {e}")
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

            if await self.is_logged_in(page):
                print("Already logged in to X.com")
                await self.save_session(page, self.platform_name)
                return True

            await page.goto(self.login_url, wait_until="networkidle")

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
                print("Automated login not fully implemented, use interactive mode.")
                return False

        except Exception as e:
            print(f"X.com login failed: {e}")
            return False
        finally:
            await page.close()
            self.headless = original_headless

    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to X."""
        page = await self.create_page(self.platform_name)
        try:
            await page.goto(self.base_url, wait_until="networkidle")

            if not await self.is_logged_in(page):
                return {"success": False, "error": "Authentication required"}

            try:
                compose_btn = await self.wait_for_element(page, '[data-testid="SideNav_NewTweet_Button"]')
                await compose_btn.click()
                await self.wait_for_element(page, '[data-testid="tweetTextarea_0"]')
            except Exception as e:
                return {"success": False, "error": f"Could not open compose dialog: {e}"}

            text = content.get("text", "")
            link = content.get("link", "")
            full_text = f"{text} {link}".strip()

            if len(full_text) > self.max_text_length:
                 return {"success": False, "error": f"Text too long: {len(full_text)}/{self.max_text_length}"}

            await self.type_text(page, '[data-testid="tweetTextarea_0"]', full_text)

            await page.wait_for_timeout(2000)

            submit_btn = await self.wait_for_element(page, '[data-testid="tweetButtonInline"]')
            await submit_btn.click()

            try:
                await page.wait_for_url(lambda url: "/status/" in url, timeout=15000)
                return {
                    "success": True,
                    "url": page.url,
                    "platform": "x"
                }
            except:
                return {"success": False, "error": "Post timeout - URL did not change to status"}

        except Exception as e:
            return {"success": False, "error": str(e), "platform": "x"}
        finally:
            await page.close()
