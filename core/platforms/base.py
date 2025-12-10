from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from core.automation import BrowserAutomation

class BasePlatform(BrowserAutomation, ABC):
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        super().__init__(options)
        self.platform_name = ""
        self.base_url = ""

    @abstractmethod
    async def is_logged_in(self, page) -> bool:
        """Check if user is logged in."""
        pass

    @abstractmethod
    async def login(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Perform login."""
        pass

    @abstractmethod
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content."""
        pass

    async def login_interactive_browserless(self) -> Tuple[Optional[str], Any, Any]:
        """
        Starts an interactive Browserless session.
        Returns: (debugger_url, browser, page)
        """
        if not self.browserless_token:
            return None, None, None

        # Ensure we use browserless for this call
        self.use_browserless = True

        # Launch browser (which calls create_browserless_session)
        browser = await self.launch_browser()
        if not browser or not self.browserless_session_id:
            return None, None, None

        # We need the debugger URL.
        # Since launch_browser abstracts the session creation, we might need to fetch it
        # or we assume we can construct it if we have the ID.
        # Construct debugger URL:
        # https://chrome.browserless.io/live/{session_id}?token={token}
        # Note: "production-sfo.browserless.io" sessions might need specific live URL base.
        # Standard: https://chrome.browserless.io/live/... works for most.
        debugger_url = f"https://chrome.browserless.io/live/{self.browserless_session_id}?token={self.browserless_token}"

        # Navigate to login page
        page = await self.create_page(self.platform_name)
        await page.goto(self.base_url) # Start at base, allowing user to navigate to login

        return debugger_url, browser, page
