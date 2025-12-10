import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

class SessionManager:
    def __init__(self, sessions_path: Optional[str] = None):
        if sessions_path:
            self.sessions_path = sessions_path
        else:
            self.sessions_path = os.path.join(os.path.expanduser("~"), ".config", "social-poster", "sessions.json")

        self.sessions: Dict[str, Any] = self.load_sessions()

    def load_sessions(self) -> Dict[str, Any]:
        """Load sessions from file."""
        if not os.path.exists(self.sessions_path):
            return {}

        try:
            with open(self.sessions_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load sessions from {self.sessions_path}: {e}")
            return {}

    def save_sessions(self) -> Dict[str, Any]:
        """Save sessions to file."""
        try:
            sessions_dir = os.path.dirname(self.sessions_path)
            if not os.path.exists(sessions_dir):
                os.makedirs(sessions_dir, exist_ok=True)

            with open(self.sessions_path, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2)

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_session(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get session for a platform."""
        return self.sessions.get(platform)

    def set_session(self, platform: str, session: Dict[str, Any]):
        """Set session for a platform and save."""
        self.sessions[platform] = session
        self.save_sessions()

    def is_session_valid(self, platform: str, max_age_hours: int = 24) -> bool:
        """Check if session is valid for a platform."""
        session = self.get_session(platform)
        if not session:
            return False

        # Check cookies
        cookies = session.get("cookies", [])
        if not cookies or not isinstance(cookies, list) or len(cookies) == 0:
            return False

        # Check expiration
        last_validated = session.get("lastValidated")
        if not last_validated:
            return False

        try:
            # Parse ISO format string
            last_val_time = datetime.fromisoformat(last_validated.replace("Z", "+00:00"))
            # Make sure we compare offset-aware datetimes if possible, or naive if both are naive.
            # datetime.now() is naive by default. datetime.utcnow() is also naive.
            # Best practice: use offset-aware UTC.
            now = datetime.now().astimezone()

            # If stored time has no tzinfo, assume it's UTC or local?
            # The JS code used new Date().toISOString() which creates '2023-01-01T00:00:00.000Z'.
            # python's fromisoformat parses the Z as UTC offset.

            # Simple expiry check
            age = now - last_val_time
            if age > timedelta(hours=max_age_hours):
                return False

            return True
        except Exception as e:
            print(f"Error validating session time: {e}")
            return False

    def clear_session(self, platform: str):
        """Clear session for a platform."""
        if platform in self.sessions:
            del self.sessions[platform]
            self.save_sessions()

    def get_valid_platforms(self) -> list[str]:
        """Get all platforms with valid sessions."""
        return [p for p in self.sessions.keys() if self.is_session_valid(p)]
