import sqlite3
from typing import Optional, Dict, Any, Tuple
from utils.helpers import now_ts
from utils.logger import get_logger
from models.types import ModData

DB_SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS mods (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author_id TEXT,
    author_name TEXT,
    file_size INTEGER,
    time_created INTEGER,
    time_updated INTEGER,
    last_checked INTEGER,
    description TEXT,
    views INTEGER,
    subscriptions INTEGER,
    favorites INTEGER,
    tags TEXT,
    visibility INTEGER,
    preview_url TEXT
);
CREATE INDEX IF NOT EXISTS idx_mods_updated ON mods(time_updated);
CREATE TABLE IF NOT EXISTS steam_users (
    steam_id TEXT PRIMARY KEY,
    persona_name TEXT,
    real_name TEXT,
    profile_url TEXT,
    avatar_url TEXT,
    last_fetched INTEGER,
    fetch_failed INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_users_last_fetched ON steam_users(last_fetched);
"""

# Module-level logger
logger = get_logger()

def connect_db(path: str) -> sqlite3.Connection:
    """Connect to SQLite database and initialize schema."""
    try:
        logger.debug(f"Connecting to database: {path}")
        conn = sqlite3.connect(path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.executescript(DB_SCHEMA)
        logger.debug("Database connection established and schema initialized")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database {path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to database {path}: {e}")
        raise

def upsert_mod(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    """Insert or update mod data in the database."""
    logger = get_logger()
    
    try:
        conn.execute(
            """
            INSERT INTO mods (id, title, author_id, author_name, file_size, time_created, time_updated, last_checked,
                             description, views, subscriptions, favorites, tags, visibility, preview_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                author_id=excluded.author_id,
                author_name=excluded.author_name,
                file_size=excluded.file_size,
                time_created=excluded.time_created,
                time_updated=excluded.time_updated,
                last_checked=excluded.last_checked,
                description=excluded.description,
                views=excluded.views,
                subscriptions=excluded.subscriptions,
                favorites=excluded.favorites,
                tags=excluded.tags,
                visibility=excluded.visibility,
                preview_url=excluded.preview_url
            """,
            (
                row["id"],
                row.get("title"),
                row.get("author_id"),
                row.get("author_name"),
                row.get("file_size"),
                row.get("time_created"),
                row.get("time_updated"),
                row.get("last_checked"),
                row.get("description"),
                row.get("views"),
                row.get("subscriptions"),
                row.get("favorites"),
                row.get("tags"),
                row.get("visibility"),
                row.get("preview_url"),
            ),
        )
        logger.debug(f"Upserted mod {row['id']}: {row.get('title', 'Unknown')}")
        
    except sqlite3.Error as e:
        logger.error(f"Failed to upsert mod {row.get('id', 'unknown')}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error upserting mod {row.get('id', 'unknown')}: {e}")
        raise

def get_known(conn: sqlite3.Connection, mid: int) -> Optional[Tuple]:
    """Get the last known update timestamp for a mod."""
    cur = conn.execute("SELECT time_updated FROM mods WHERE id = ?", (mid,))
    return cur.fetchone()

def get_mod_by_id(conn: sqlite3.Connection, mod_id: int) -> Optional[Dict[str, Any]]:
    """Get complete mod data as dictionary."""
    cur = conn.execute("SELECT * FROM mods WHERE id = ?", (mod_id,))
    row = cur.fetchone()
    return dict(row) if row else None

def get_steam_user(conn: sqlite3.Connection, steam_id: str) -> Optional[Tuple]:
    """Get cached Steam user data from database."""
    cur = conn.execute("SELECT persona_name, real_name, profile_url, avatar_url, last_fetched, fetch_failed FROM steam_users WHERE steam_id = ?", (steam_id,))
    return cur.fetchone()

def upsert_steam_user(conn: sqlite3.Connection, user_data: Dict[str, Any]) -> None:
    """Insert or update Steam user data in the database."""
    conn.execute(
        """
        INSERT INTO steam_users (steam_id, persona_name, real_name, profile_url, avatar_url, last_fetched, fetch_failed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(steam_id) DO UPDATE SET
            persona_name=excluded.persona_name,
            real_name=excluded.real_name,
            profile_url=excluded.profile_url,
            avatar_url=excluded.avatar_url,
            last_fetched=excluded.last_fetched,
            fetch_failed=excluded.fetch_failed
        """,
        (
            user_data["steam_id"],
            user_data.get("persona_name"),
            user_data.get("real_name"),
            user_data.get("profile_url"),
            user_data.get("avatar_url"),
            user_data["last_fetched"],
            user_data.get("fetch_failed", 0),
        ),
    )

def mark_steam_user_fetch_failed(conn: sqlite3.Connection, steam_id: str) -> None:
    """Mark a Steam user fetch as failed to avoid repeated attempts."""
    conn.execute(
        """
        INSERT INTO steam_users (steam_id, last_fetched, fetch_failed)
        VALUES (?, ?, 1)
        ON CONFLICT(steam_id) DO UPDATE SET
            last_fetched=excluded.last_fetched,
            fetch_failed=1
        """,
        (steam_id, now_ts()),
    )
