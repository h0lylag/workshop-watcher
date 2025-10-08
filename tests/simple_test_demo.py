#!/usr/bin/env python3
"""
Simple test runner that doesn't require pytest.
Shows how tests work using Python's built-in unittest.

Run: python tests/simple_test_demo.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import get_current_timestamp, chunk_list, create_empty_mod_record
from utils.validators import validate_steam_api_key, validate_discord_webhook


def test_chunk_list():
    """Test that chunk_list splits lists correctly."""
    print("Testing chunk_list()...")
    
    # Test 1: Basic chunking
    items = [1, 2, 3, 4, 5]
    result = list(chunk_list(items, 2))
    expected = [[1, 2], [3, 4], [5]]
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✅ Basic chunking works")
    
    # Test 2: Empty list
    result = list(chunk_list([], 2))
    assert result == [], "Empty list should return empty list"
    print("  ✅ Empty list handled correctly")
    
    # Test 3: Chunk size = 1
    result = list(chunk_list([1, 2, 3], 1))
    expected = [[1], [2], [3]]
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✅ Chunk size 1 works")
    
    print("  ✅ All chunk_list tests passed!\n")


def test_get_current_timestamp():
    """Test that get_current_timestamp returns valid timestamps."""
    print("Testing get_current_timestamp()...")
    
    # Test 1: Returns integer
    result = get_current_timestamp()
    assert isinstance(result, int), f"Expected int, got {type(result)}"
    print("  ✅ Returns integer")
    
    # Test 2: Returns reasonable value (after 2020)
    assert result > 1577836800, "Timestamp should be after 2020"
    print("  ✅ Returns reasonable timestamp")
    
    print("  ✅ All timestamp tests passed!\n")


def test_create_empty_mod_record():
    """Test that create_empty_mod_record creates valid records."""
    print("Testing create_empty_mod_record()...")
    
    # Test 1: Has required fields
    result = create_empty_mod_record(123)
    assert result["id"] == 123, f"Expected id=123, got {result['id']}"
    print("  ✅ Has correct ID")
    
    # Test 2: Has timestamp
    assert "last_checked" in result, "Missing last_checked field"
    assert isinstance(result["last_checked"], int), "last_checked should be int"
    print("  ✅ Has last_checked timestamp")
    
    # Test 3: Other fields are None
    assert result["title"] is None, "title should be None"
    assert result["author_id"] is None, "author_id should be None"
    print("  ✅ Other fields are None")
    
    print("  ✅ All empty record tests passed!\n")


def test_steam_api_key_validator():
    """Test Steam API key validation."""
    print("Testing validate_steam_api_key()...")
    
    # Test 1: Valid key
    valid_key = "A1B2C3D4E5F67890A1B2C3D4E5F67890"
    assert validate_steam_api_key(valid_key) is True, "Should accept valid key"
    print("  ✅ Accepts valid 32-char hex key")
    
    # Test 2: Invalid - too short
    short_key = "ABC123"
    assert validate_steam_api_key(short_key) is False, "Should reject short key"
    print("  ✅ Rejects short key")
    
    # Test 3: Invalid - non-hex characters
    invalid_key = "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
    assert validate_steam_api_key(invalid_key) is False, "Should reject non-hex"
    print("  ✅ Rejects non-hex characters")
    
    # Test 4: Invalid - None
    assert validate_steam_api_key(None) is False, "Should reject None"
    print("  ✅ Rejects None")
    
    print("  ✅ All API key validation tests passed!\n")


def test_discord_webhook_validator():
    """Test Discord webhook validation."""
    print("Testing validate_discord_webhook()...")
    
    # Test 1: Valid webhook
    valid_url = "https://discord.com/api/webhooks/123456789/abcdefghijk"
    assert validate_discord_webhook(valid_url) is True, "Should accept valid webhook"
    print("  ✅ Accepts valid Discord webhook")
    
    # Test 2: Invalid domain
    invalid_url = "https://example.com/api/webhooks/123/abc"
    assert validate_discord_webhook(invalid_url) is False, "Should reject wrong domain"
    print("  ✅ Rejects non-Discord domain")
    
    # Test 3: Invalid - not HTTPS
    http_url = "http://discord.com/api/webhooks/123/abc"
    assert validate_discord_webhook(http_url) is False, "Should reject HTTP"
    print("  ✅ Rejects non-HTTPS URL")
    
    # Test 4: Invalid - None
    assert validate_discord_webhook(None) is False, "Should reject None"
    print("  ✅ Rejects None")
    
    print("  ✅ All webhook validation tests passed!\n")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Running Workshop Watcher Tests")
    print("=" * 60 + "\n")
    
    try:
        test_chunk_list()
        test_get_current_timestamp()
        test_create_empty_mod_record()
        test_steam_api_key_validator()
        test_discord_webhook_validator()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
