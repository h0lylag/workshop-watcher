"""
Tests for database functions.

Run with: python -m unittest tests/test_db.py -v
"""
import sys
import sqlite3
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.db import (
    connect_db,
    upsert_mod,
    get_last_update_time,
    get_mod_by_id,
    get_cached_steam_users
)


class TestDatabaseConnection(unittest.TestCase):
    """Tests for connect_db()."""
    
    def test_creates_database_file(self):
        """Should create database file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "new_db.db"
            conn = connect_db(str(db_path))
            
            self.assertTrue(db_path.exists())
            conn.close()
    
    def test_creates_mods_table(self):
        """Should create mods table with correct schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='mods'"
            )
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0], "mods")
            conn.close()
    
    def test_creates_steam_users_table(self):
        """Should create steam_users table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='steam_users'"
            )
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            conn.close()


class TestUpsertMod(unittest.TestCase):
    """Tests for upsert_mod()."""
    
    def test_insert_new_mod(self):
        """Should insert a new mod."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            mod_data = {
                "id": 123,
                "title": "Test Mod",
                "author_id": "76561198000000000",
                "time_updated": 1234567890,
                "last_checked": 1234567890
            }
            
            upsert_mod(conn, mod_data)
            
            # Check it was inserted
            result = get_mod_by_id(conn, 123)
            self.assertIsNotNone(result)
            self.assertEqual(result["title"], "Test Mod")
            conn.close()
    
    def test_update_existing_mod(self):
        """Should update an existing mod."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            # Insert initial mod
            mod_data = {
                "id": 456,
                "title": "Original Title",
                "time_updated": 1000000,
                "last_checked": 1000000
            }
            upsert_mod(conn, mod_data)
            
            # Update it
            updated_data = {
                "id": 456,
                "title": "Updated Title",
                "time_updated": 2000000,
                "last_checked": 2000000
            }
            upsert_mod(conn, updated_data)
            
            # Check it was updated
            result = get_mod_by_id(conn, 456)
            self.assertEqual(result["title"], "Updated Title")
            self.assertEqual(result["time_updated"], 2000000)
            conn.close()
    
    def test_handles_optional_fields(self):
        """Should handle None values for optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            mod_data = {
                "id": 789,
                "title": None,
                "author_id": None,
                "file_size": None,
                "last_checked": 1234567890
            }
            
            upsert_mod(conn, mod_data)
            
            result = get_mod_by_id(conn, 789)
            self.assertIsNotNone(result)
            self.assertIsNone(result["title"])
            conn.close()


class TestGetLastUpdateTime(unittest.TestCase):
    """Tests for get_last_update_time()."""
    
    def test_returns_update_time_for_existing_mod(self):
        """Should return time_updated for existing mod."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            mod_data = {
                "id": 123,
                "time_updated": 9999999,
                "last_checked": 1234567890
            }
            upsert_mod(conn, mod_data)
            
            result = get_last_update_time(conn, 123)
            self.assertEqual(result, 9999999)
            conn.close()
    
    def test_returns_none_for_nonexistent_mod(self):
        """Should return None if mod doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            result = get_last_update_time(conn, 999999)
            self.assertIsNone(result)
            conn.close()
    
    def test_returns_none_for_null_time_updated(self):
        """Should return None if time_updated is NULL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            mod_data = {
                "id": 456,
                "time_updated": None,
                "last_checked": 1234567890
            }
            upsert_mod(conn, mod_data)
            
            result = get_last_update_time(conn, 456)
            self.assertIsNone(result)
            conn.close()


class TestGetModByID(unittest.TestCase):
    """Tests for get_mod_by_id()."""
    
    def test_returns_complete_mod_data(self):
        """Should return full mod record as dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            mod_data = {
                "id": 123,
                "title": "Complete Mod",
                "author_id": "76561198000000000",
                "author_name": "Test Author",
                "file_size": 1048576,
                "time_created": 1000000,
                "time_updated": 2000000,
                "last_checked": 3000000,
                "description": "Test description",
                "views": 100,
                "subscriptions": 50,
                "favorites": 25,
                "tags": "tag1,tag2",
                "visibility": 0,
                "preview_url": "https://example.com/preview.jpg"
            }
            upsert_mod(conn, mod_data)
            
            result = get_mod_by_id(conn, 123)
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["title"], "Complete Mod")
            self.assertEqual(result["author_name"], "Test Author")
            self.assertEqual(result["file_size"], 1048576)
            conn.close()
    
    def test_returns_none_for_nonexistent_mod(self):
        """Should return None if mod doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            result = get_mod_by_id(conn, 999999)
            self.assertIsNone(result)
            conn.close()


class TestGetCachedSteamUsers(unittest.TestCase):
    """Tests for get_cached_steam_users()."""
    
    def test_returns_empty_list_for_empty_input(self):
        """Should return empty list when given empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            result = get_cached_steam_users(conn, [])
            self.assertEqual(result, [])
            conn.close()
    
    def test_returns_user_data_for_single_id(self):
        """Should return data for single Steam ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            # Insert a user
            conn.execute(
                """INSERT INTO steam_users (steam_id, persona_name, last_fetched, fetch_failed)
                   VALUES (?, ?, ?, ?)""",
                ("76561198000000001", "TestUser", 1234567890, 0)
            )
            
            result = get_cached_steam_users(conn, ["76561198000000001"])
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][0], "76561198000000001")  # steam_id
            self.assertEqual(result[0][3], "TestUser")  # persona_name
            conn.close()
    
    def test_returns_multiple_users(self):
        """Should return data for multiple Steam IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            # Insert multiple users
            users = [
                ("76561198000000001", "User1", 1234567890, 0),
                ("76561198000000002", "User2", 1234567891, 0),
                ("76561198000000003", "User3", 1234567892, 0),
            ]
            for user in users:
                conn.execute(
                    """INSERT INTO steam_users (steam_id, persona_name, last_fetched, fetch_failed)
                       VALUES (?, ?, ?, ?)""",
                    user
                )
            
            result = get_cached_steam_users(conn, [
                "76561198000000001",
                "76561198000000002",
                "76561198000000003"
            ])
            
            self.assertEqual(len(result), 3)
            conn.close()
    
    def test_returns_only_matching_users(self):
        """Should only return users that exist in database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = connect_db(str(db_path))
            
            # Insert one user
            conn.execute(
                """INSERT INTO steam_users (steam_id, persona_name, last_fetched, fetch_failed)
                   VALUES (?, ?, ?, ?)""",
                ("76561198000000001", "ExistingUser", 1234567890, 0)
            )
            
            # Query for two users (one exists, one doesn't)
            result = get_cached_steam_users(conn, [
                "76561198000000001",
                "76561198000000999"  # Doesn't exist
            ])
            
            # Should only return the one that exists
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][0], "76561198000000001")
            conn.close()


if __name__ == '__main__':
    unittest.main()
