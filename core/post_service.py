import asyncio
from typing import List, Dict, Any
from core.platforms.x_platform import XPlatform
from core.platforms.facebook_platform import FacebookPlatform
from core.history_manager import HistoryManager

class PostService:
    def __init__(self):
        self.platforms = {
            "x": XPlatform(),
            "facebook": FacebookPlatform()
        }
        self.history_manager = HistoryManager()

    async def post_to_platform(self, platform_name: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post to a single platform."""
        platform = self.platforms.get(platform_name)
        if not platform:
            result = {"success": False, "error": "Unknown platform"}
        else:
            result = await platform.post(content)

        # Log to history
        self.history_manager.add_entry(platform_name, content, result)
        return result

    async def post_to_multiple(self, platform_names: List[str], content: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Post to multiple platforms concurrently."""
        tasks = []
        for name in platform_names:
            tasks.append(self.post_to_platform(name, content))

        results_list = await asyncio.gather(*tasks)

        results = {}
        for name, res in zip(platform_names, results_list):
            results[name] = res

        return results

    def get_supported_platforms(self) -> List[str]:
        return list(self.platforms.keys())
