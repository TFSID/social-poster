import unittest
import os
import shutil
import json
from unittest.mock import patch, MagicMock
from core.session_manager import SessionManager
from core.history_manager import HistoryManager
from core.ai_service import AIService

class TestCoreModules(unittest.TestCase):
    def setUp(self):
        # Create temp dir for tests
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)
        self.sessions_path = os.path.join(self.test_dir, "sessions.json")
        self.history_path = os.path.join(self.test_dir, "history.db")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_session_manager(self):
        sm = SessionManager(self.sessions_path)

        # Test save and load
        session_data = {"cookies": [{"name": "test", "value": "123"}], "lastValidated": "2023-01-01T00:00:00Z"}
        sm.set_session("test_platform", session_data)

        # Reload
        sm2 = SessionManager(self.sessions_path)
        loaded_session = sm2.get_session("test_platform")
        self.assertEqual(loaded_session["cookies"][0]["value"], "123")

        # Test validation (should be expired)
        self.assertFalse(sm2.is_session_valid("test_platform"))

    def test_history_manager(self):
        hm = HistoryManager(self.history_path)

        content = {"text": "Hello", "link": "http://example.com"}
        result = {"success": True, "url": "http://x.com/status/123"}

        hm.add_entry("x", content, result)

        df = hm.get_history()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["platform"], "x")
        self.assertEqual(df.iloc[0]["success"], 1)

    @patch("core.ai_service.OpenAI")
    def test_ai_service(self, mock_openai):
        service = AIService(api_key="fake-key")

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Viral Post Content"
        mock_response.usage.total_tokens = 10
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        result = service.generate_viral_post("Test prompt")

        self.assertTrue(result["success"])
        self.assertEqual(result["content"]["text"], "Viral Post Content")

if __name__ == "__main__":
    unittest.main()
