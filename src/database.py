import os
import aiosqlite
from datetime import datetime

DB_PATH = os.path.join("data", "bot.db")


async def init_db(db_path: str = DB_PATH):
    """Initialize SQLite database and create required tables."""
    dirname = os.path.dirname(db_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TEXT
            )
        """)

        # Search History / Logs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                timestamp TEXT,
                status TEXT
            )
        """)

        # Cached File References table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cached_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT,
                file_path TEXT,
                source_type TEXT,
                expires_at TEXT
            )
        """)
        await db.commit()


async def upsert_user(user_id: int, username: str, first_name: str, db_path: str = DB_PATH):
    """Insert or update user record."""
    created_at = datetime.utcnow().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name, created_at))
        await db.commit()


async def log_search(user_id: int, query: str, status: str = "SUCCESS", db_path: str = DB_PATH):
    """Log a user search query."""
    timestamp = datetime.utcnow().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO search_logs (user_id, query, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (user_id, query, timestamp, status))
        await db.commit()


async def cache_file_reference(file_id: str, file_path: str, source_type: str, expires_at: str = None, db_path: str = DB_PATH):
    """Cache a file reference."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO cached_files (file_id, file_path, source_type, expires_at)
            VALUES (?, ?, ?, ?)
        """, (file_id, file_path, source_type, expires_at))
        await db.commit()


async def get_user(user_id: int, db_path: str = DB_PATH):
    """Retrieve user record by user_id."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT user_id, username, first_name, created_at FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "first_name": row[2],
                    "created_at": row[3]
                }
            return None


async def get_search_logs(user_id: int, db_path: str = DB_PATH):
    """Retrieve search logs for a user."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT id, user_id, query, timestamp, status FROM search_logs WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "user_id": r[1],
                    "query": r[2],
                    "timestamp": r[3],
                    "status": r[4]
                }
                for r in rows
            ]
