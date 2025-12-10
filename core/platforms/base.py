from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.automation import BrowserAutomation

class BasePlatform(BrowserAutomation, ABC):
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        super().__init__(options)
        self.platform_name = "" # Override in subclass
        self.base_url = "" # Override in subclass

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
