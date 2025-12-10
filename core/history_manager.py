import sqlite3
import pandas as pd
from datetime import datetime
import os
from typing import Dict, Any, List

class HistoryManager:
    def __init__(self, db_path: str = "history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                platform TEXT,
                content_text TEXT,
                content_link TEXT,
                success BOOLEAN,
                error_message TEXT,
                post_url TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_entry(self, platform: str, content: Dict[str, Any], result: Dict[str, Any]):
        """Add a post entry to history."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        timestamp = datetime.now().isoformat()
        success = result.get("success", False)
        error = result.get("error", "")
        post_url = result.get("url", "")
        text = content.get("text", "")
        link = content.get("link", "")

        c.execute('''
            INSERT INTO posts (timestamp, platform, content_text, content_link, success, error_message, post_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, platform, text, link, success, error, post_url))

        conn.commit()
        conn.close()

    def get_history(self) -> pd.DataFrame:
        """Get history as DataFrame."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM posts ORDER BY timestamp DESC", conn)
            conn.close()
            return df
        except Exception:
            return pd.DataFrame()

    def get_stats(self) -> Dict[str, Any]:
        """Get basic statistics."""
        df = self.get_history()
        if df.empty:
            return {
                "total_posts": 0,
                "success_rate": 0,
                "platform_breakdown": {}
            }

        total = len(df)
        successful = len(df[df['success'] == 1])
        rate = (successful / total) * 100

        breakdown = df['platform'].value_counts().to_dict()

        return {
            "total_posts": total,
            "success_rate": round(rate, 2),
            "platform_breakdown": breakdown
        }
