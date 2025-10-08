"""
Tests for database functions.

Run with: pytest tests/test_db.py -v
"""
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.db import (
    connect_db,
    upsert_mod,
    get_last_update_time,
    get_mod_by_id,
    get_cached_steam_users
)


# pytest fixtures - these run before each test
import pytest

@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary test database for each test."""
    db_path = tmp_path / "test.db"
    conn = connect_db(str(db_path))
    yield conn  # This is where the test runs
    conn.close()  # Cleanup after test


class TestDatabaseConnection:
    """Tests for connect_db()."""
    
    def test_creates_database_file(self, tmp_path):
        """Should create database file if it doesn't exist."""
        db_path = tmp_path / "new_db.db"
        conn = connect_db(str(db_path))
        
        assert db_path.exists()
        conn.close()
    
    def test_creates_mods_table(self, temp_db):
        """Should create mods table with correct schema."""
        cursor = temp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mods'"
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "mods"
    
    def test_creates_steam_users_table(self, temp_db):
        """Should create steam_users table."""
        cursor = temp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='steam_users'"
        )
        result = cursor.fetchone()
        
        assert result is not None


class TestUpsertMod:
    """Tests for upsert_mod()."""
    
    def test_insert_new_mod(self, temp_db):
        """Should insert a new mod."""
        mod_data = {
            "id": 123,
            "title": "Test Mod",
            "author_id": "76561198000000000",
            "time_updated": 1234567890,
            "last_checked": 1234567890
        }
        
        upsert_mod(temp_db, mod_data)
        
        # Check it was inserted
        result = get_mod_by_id(temp_db, 123)
        assert result is not None
        assert result["title"] == "Test Mod"
    
    def test_update_existing_mod(self, temp_db):
        """Should update an existing mod."""
        # Insert initial mod
        mod_data = {
            "id": 456,
            "title": "Original Title",
            "time_updated": 1000000,
            "last_checked": 1000000
        }
        upsert_mod(temp_db, mod_data)
        
        # Update it
        updated_data = {
            "id": 456,
            "title": "Updated Title",
            "time_updated": 2000000,
            "last_checked": 2000000
        }
        upsert_mod(temp_db, updated_data)
        
        # Check it was updated
        result = get_mod_by_id(temp_db, 456)
        assert result["title"] == "Updated Title"
        assert result["time_updated"] == 2000000
    
    def test_handles_optional_fields(self, temp_db):
        """Should handle None values for optional fields."""
        mod_data = {
            "id": 789,
            "title": None,
            "author_id": None,
            "file_size": None,
            "last_checked": 1234567890
        }
        
        upsert_mod(temp_db, mod_data)
        
        result = get_mod_by_id(temp_db, 789)
        assert result is not None
        assert result["title"] is None


class TestGetLastUpdateTime:
    """Tests for get_last_update_time()."""
    
    def test_returns_update_time_for_existing_mod(self, temp_db):
        """Should return time_updated for existing mod."""
        mod_data = {
            "id": 123,
            "time_updated": 9999999,
            "last_checked": 1234567890
        }
        upsert_mod(temp_db, mod_data)
        
        result = get_last_update_time(temp_db, 123)
        assert result == 9999999
    
    def test_returns_none_for_nonexistent_mod(self, temp_db):
        """Should return None if mod doesn't exist."""
        result = get_last_update_time(temp_db, 999999)
        assert result is None
    
    def test_returns_none_for_null_time_updated(self, temp_db):
        """Should return None if time_updated is NULL."""
        mod_data = {
            "id": 456,
            "time_updated": None,
            "last_checked": 1234567890
        }
        upsert_mod(temp_db, mod_data)
        
        result = get_last_update_time(temp_db, 456)
        assert result is None


class TestGetModByID:
    """Tests for get_mod_by_id()."""
    
    def test_returns_complete_mod_data(self, temp_db):
        """Should return full mod record as dictionary."""
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
        upsert_mod(temp_db, mod_data)
        
        result = get_mod_by_id(temp_db, 123)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["title"] == "Complete Mod"
        assert result["author_name"] == "Test Author"
        assert result["file_size"] == 1048576
    
    def test_returns_none_for_nonexistent_mod(self, temp_db):
        """Should return None if mod doesn't exist."""
        result = get_mod_by_id(temp_db, 999999)
        assert result is None


class TestGetCachedSteamUsers:
    """Tests for get_cached_steam_users()."""
    
    def test_returns_empty_list_for_empty_input(self, temp_db):
        """Should return empty list when given empty list."""
        result = get_cached_steam_users(temp_db, [])
        assert result == []
    
    def test_returns_user_data_for_single_id(self, temp_db):
        """Should return data for single Steam ID."""
        # Insert a user
        temp_db.execute(
            """INSERT INTO steam_users (steam_id, persona_name, last_fetched, fetch_failed)
               VALUES (?, ?, ?, ?)""",
            ("76561198000000001", "TestUser", 1234567890, 0)
        )
        
        result = get_cached_steam_users(temp_db, ["76561198000000001"])
        
        assert len(result) == 1
        assert result[0][0] == "76561198000000001"  # steam_id
        assert result[0][3] == "TestUser"  # persona_name
    
    def test_returns_multiple_users(self, temp_db):
        """Should return data for multiple Steam IDs."""
        # Insert multiple users
        users = [
            ("76561198000000001", "User1", 1234567890, 0),
            ("76561198000000002", "User2", 1234567891, 0),
            ("76561198000000003", "User3", 1234567892, 0),
        ]
        for user in users:
            temp_db.execute(
                """INSERT INTO steam_users (steam_id, persona_name, last_fetched, fetch_failed)
                   VALUES (?, ?, ?, ?)""",
                user
            )
        
        result = get_cached_steam_users(temp_db, [
            "76561198000000001",
            "76561198000000002",
            "76561198000000003"
        ])
        
        assert len(result) == 3
    
    def test_returns_only_matching_users(self, temp_db):
        """Should only return users that exist in database."""
        # Insert one user
        temp_db.execute(
            """INSERT INTO steam_users (steam_id, persona_name, last_fetched, fetch_failed)
               VALUES (?, ?, ?, ?)""",
            ("76561198000000001", "ExistingUser", 1234567890, 0)
        )
        
        # Query for two users (one exists, one doesn't)
        result = get_cached_steam_users(temp_db, [
            "76561198000000001",
            "76561198000000999"  # Doesn't exist
        ])
        
        # Should only return the one that exists
        assert len(result) == 1
        assert result[0][0] == "76561198000000001"


# To run these tests:
# 1. Install pytest: pip install pytest
# 2. Run: pytest tests/test_db.py -v
#
# Example output:
# tests/test_db.py::TestDatabaseConnection::test_creates_database_file PASSED
# tests/test_db.py::TestUpsertMod::test_insert_new_mod PASSED
# tests/test_db.py::TestGetLastUpdateTime::test_returns_update_time_for_existing_mod PASSED
# ... etc
