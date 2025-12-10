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

            # Check for specific elements present when logged in
            # Sidebar navigation, profile icon, etc.
            try:
                # Top right profile icon or menu
                await page.wait_for_selector('div[role="banner"]', timeout=3000)
                # Or look for 'input[aria-label="Search Facebook"]'
                # Or just check if we are NOT on a login page and have some feed content
                if await page.query_selector('div[role="feed"]'):
                    return True
                if await page.query_selector('[aria-label="Account controls and settings"]'):
                    return True
                return False
            except:
                return False
        except Exception as e:
            print(f"Failed to check login status for Facebook: {e}")
            return False

    async def login(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Perform login.
        Interactive mode supported.
        """
        options = options or {}
        original_headless = self.headless
        if "headless" in options:
            self.headless = options["headless"]
            if self.browser:
                await self.close_browser()

        page = await self.create_page(self.platform_name)

        try:
            await page.goto(self.base_url, wait_until="networkidle")

            # Handle cookie consent if it appears
            try:
                # Common selector for "Allow all cookies" on FB
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

            # Navigate to create post
            # Facebook DOM is very complex and dynamic.
            # 1. Click "What's on your mind, [Name]?"
            try:
                # Try to find the input that triggers the post modal
                create_post_trigger = await page.wait_for_selector('div[role="button"] span:has-text("What\'s on your mind")', timeout=5000)
                if not create_post_trigger:
                     # Fallback selector strategies
                     create_post_trigger = await page.wait_for_selector('div[role="button"] span:has-text("What")', timeout=1000)

                await create_post_trigger.click()
            except Exception as e:
                # Try hitting 'p' key which is a shortcut sometimes? No, that's unreliable.
                return {"success": False, "error": f"Could not find 'Create Post' trigger: {e}"}

            # 2. Wait for modal
            try:
                # The dialog usually has role="dialog" and label "Create post"
                modal = await page.wait_for_selector('div[role="dialog"][aria-label="Create post"]', timeout=5000)
                # The text input is a contenteditable div
                input_area = await modal.wait_for_selector('div[contenteditable="true"][role="textbox"]', timeout=2000)
            except Exception as e:
                 return {"success": False, "error": f"Could not find post modal/input: {e}"}

            text = content.get("text", "")
            link = content.get("link", "")
            full_text = f"{text}\n\n{link}".strip()

            await input_area.click()
            await page.keyboard.type(full_text)

            # Wait for link preview if link exists
            if link:
                await page.wait_for_timeout(3000)

            # 3. Click Post button
            # Usually has aria-label="Post"
            try:
                post_btn = await modal.wait_for_selector('div[aria-label="Post"]', timeout=2000)
                # Ensure it's not disabled (sometimes disabled until text is typed)
                # Playwright's click checks for this
                await post_btn.click()
            except Exception as e:
                return {"success": False, "error": f"Could not find or click 'Post' button: {e}"}

            # 4. Wait for posting to complete
            # The modal should disappear
            try:
                await page.wait_for_selector('div[role="dialog"][aria-label="Create post"]', state="hidden", timeout=10000)
                return {
                    "success": True,
                    "platform": "facebook",
                    "timestamp": datetime.now().isoformat()
                }
            except:
                return {"success": False, "error": "Post timeout - Modal did not close"}

        except Exception as e:
            return {"success": False, "error": str(e), "platform": "facebook"}
        finally:
            await page.close()
