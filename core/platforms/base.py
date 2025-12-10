from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from core.browserless import BrowserlessService
import asyncio

class BasePlatform(ABC):
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options = options or {}
        self.browserless_token = self.options.get("browserless_token")
        self.platform_name = ""
        self.base_url = ""

        if self.browserless_token:
            self.service = BrowserlessService(self.browserless_token)
        else:
            self.service = None

    @abstractmethod
    async def login_interactive_browserless(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Starts session. Returns (live_url, session_id, ws_url).
        """
        pass

    @abstractmethod
    async def check_login_status(self, ws_url: str) -> bool:
        pass

    @abstractmethod
    async def post(self, content: Dict[str, Any], cookies: list) -> Dict[str, Any]:
        """Post content using /function API."""
        pass
