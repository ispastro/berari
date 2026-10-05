import sqlite3
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: Path):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high performance and concurrency
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Vacancies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_hash TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL,
                    deadline TEXT,
                    summary TEXT,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    notified INTEGER DEFAULT 0
                )
            """)

            # Scraper audit history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    items_found INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)

            # Telegram subscriber chat IDs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    chat_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    subscribed_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)
            conn.commit()

    @staticmethod
    def generate_hash(title: str, url: str) -> str:
        """Create a deterministic hash identifier for a vacancy based on normalized title and URL."""
        normalized = f"{title.strip().lower()}|{url.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def record_scrape(self, source: str, status: str, items_found: int = 0, error: Optional[str] = None):
        """Log a scraper run result."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO scrape_logs (timestamp, source, status, items_found, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (datetime.now(timezone.utc).isoformat(), source, status, items_found, error)
            )
            conn.commit()

    def upsert_vacancy(self, title: str, source: str, url: str, deadline: Optional[str] = None, summary: Optional[str] = None) -> Dict[str, Any]:
        """
        Insert or update a vacancy.
        Returns dict with:
          - 'is_new': True if never seen before
          - 'job_hash': Hash key
          - 'id': DB ID
        """
        job_hash = self.generate_hash(title, url)
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, notified FROM vacancies WHERE job_hash = ?", (job_hash,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE vacancies 
                    SET last_seen_at = ?, is_active = 1, deadline = COALESCE(?, deadline), summary = COALESCE(?, summary)
                    WHERE job_hash = ?
                    """,
                    (now, deadline, summary, job_hash)
                )
                conn.commit()
                return {
                    "is_new": False,
                    "already_notified": bool(existing["notified"]),
                    "job_hash": job_hash,
                    "id": existing["id"],
                }
            else:
                cursor.execute(
                    """
                    INSERT INTO vacancies (job_hash, title, source, url, deadline, summary, first_seen_at, last_seen_at, is_active, notified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
                    """,
                    (job_hash, title, source, url, deadline, summary, now, now)
                )
                conn.commit()
                new_id = cursor.lastrowid
                return {
                    "is_new": True,
                    "already_notified": False,
                    "job_hash": job_hash,
                    "id": new_id,
                }

    def mark_notified(self, job_hash: str):
        """Mark a vacancy as alerted to avoid duplicate notifications."""
        with self._get_connection() as conn:
            conn.execute("UPDATE vacancies SET notified = 1 WHERE job_hash = ?", (job_hash,))
            conn.commit()

    def get_unnotified_vacancies(self) -> List[Dict[str, Any]]:
        """Fetch all newly discovered vacancies that haven't been alerted yet."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vacancies WHERE notified = 0 AND is_active = 1 ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_vacancies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch the most recent vacancies tracked."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vacancies ORDER BY first_seen_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Return system statistics for /status command."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM vacancies")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as active FROM vacancies WHERE is_active = 1")
            active = cursor.fetchone()["active"]

            cursor.execute("SELECT COUNT(*) as subs FROM subscribers WHERE is_active = 1")
            subscribers = cursor.fetchone()["subs"]

            cursor.execute("SELECT timestamp, status, source FROM scrape_logs ORDER BY id DESC LIMIT 1")
            last_scrape = cursor.fetchone()

            return {
                "total_vacancies": total,
                "active_vacancies": active,
                "subscribers_count": subscribers,
                "last_scrape_time": last_scrape["timestamp"] if last_scrape else "Never",
                "last_scrape_status": last_scrape["status"] if last_scrape else "N/A",
                "last_scrape_source": last_scrape["source"] if last_scrape else "N/A",
            }

    def add_subscriber(self, chat_id: str, username: Optional[str] = None, first_name: Optional[str] = None) -> bool:
        """Register or reactivate a subscriber chat ID."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id FROM subscribers WHERE chat_id = ?", (chat_id,))
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE subscribers SET is_active = 1, username = ?, first_name = ? WHERE chat_id = ?",
                    (username, first_name, chat_id)
                )
                conn.commit()
                return False
            else:
                cursor.execute(
                    "INSERT INTO subscribers (chat_id, username, first_name, subscribed_at, is_active) VALUES (?, ?, ?, ?, 1)",
                    (chat_id, username, first_name, now)
                )
                conn.commit()
                return True

    def remove_subscriber(self, chat_id: str):
        """Unsubscribe a chat ID."""
        with self._get_connection() as conn:
            conn.execute("UPDATE subscribers SET is_active = 0 WHERE chat_id = ?", (chat_id,))
            conn.commit()

    def get_active_subscribers(self) -> List[str]:
        """Get all active subscriber chat IDs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id FROM subscribers WHERE is_active = 1")
            return [row["chat_id"] for row in cursor.fetchall()]
