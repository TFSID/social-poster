import json
import asyncio
import requests
import websockets
from typing import Optional, Dict, Any, List

class BrowserlessService:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://production-sfo.browserless.io"

    async def create_session(self, url: str = "about:blank") -> Optional[Dict[str, Any]]:
        """
        Creates a Browserless session using REST API.
        Returns dict with 'id', 'connect_url', 'live_url', 'ws_url'.
        """
        api_url = f"{self.base_url}/session?token={self.token}"
        config = {
            "ttl": 600000, # 10 mins
            "headless": False,
            "stealth": True
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                json=config
            ))

            if not response.ok:
                print(f"Failed to create session: {response.text}")
                return None

            data = response.json()
            session_id = data.get("id")
            # Construct derived URLs
            # Live URL: https://chrome.browserless.io/live/{id}?token={token}
            # Note: Might vary by region, but chrome.browserless.io usually routes correctly.
            live_url = f"https://chrome.browserless.io/live/{session_id}?token={self.token}"

            # WSS URL for CDP: provided in 'connect' usually, but we need raw WSS not Puppeteer endpoint?
            # 'connect' field is like: wss://.../session/connect/{id}
            ws_url = data.get("connect") # This works with generic CDP clients usually

            return {
                "id": session_id,
                "ws_url": ws_url,
                "live_url": live_url
            }
        except Exception as e:
            print(f"Error creating session: {e}")
            return None

    async def stop_session(self, session_id: str):
        """Stops the session."""
        api_url = f"{self.base_url}/session/{session_id}?token={self.token}&force=true"
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: requests.delete(api_url))
        except Exception as e:
            print(f"Error stopping session: {e}")

    async def get_cookies(self, ws_url: str) -> List[Dict[str, Any]]:
        """
        Connects via Websockets/CDP to retrieve cookies.
        """
        try:
            async with websockets.connect(ws_url) as ws:
                # Send Network.getCookies
                msg = {
                    "id": 1,
                    "method": "Network.getCookies",
                    "params": {}
                }
                await ws.send(json.dumps(msg))

                response = await ws.recv()
                data = json.loads(response)

                if "result" in data and "cookies" in data["result"]:
                    return data["result"]["cookies"]
                return []
        except Exception as e:
            print(f"Error getting cookies via CDP: {e}")
            return []

    async def check_selector(self, ws_url: str, selector: str) -> bool:
        """
        Checks if a selector exists in the DOM via CDP Runtime.evaluate.
        """
        try:
            async with websockets.connect(ws_url) as ws:
                # Evaluate JS: document.querySelector(selector)
                expression = f"!!document.querySelector('{selector}')"
                msg = {
                    "id": 2,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": expression
                    }
                }
                await ws.send(json.dumps(msg))

                response = await ws.recv()
                data = json.loads(response)

                # Result format: {result: {result: {type: 'boolean', value: true}}}
                if "result" in data and "result" in data["result"]:
                    val = data["result"]["result"].get("value", False)
                    return val
                return False
        except Exception as e:
            print(f"Error checking selector: {e}")
            return False

    async def run_function(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs a Node.js Puppeteer script via /function API.
        """
        api_url = f"{self.base_url}/function?token={self.token}"
        payload = {
            "code": code,
            "context": context or {}
        }

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                json=payload
            ))

            if response.ok:
                # Browserless returns content-type based on what the function returns
                # Usually text or json
                try:
                    return {"success": True, "data": response.json()}
                except:
                    return {"success": True, "data": response.text}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
