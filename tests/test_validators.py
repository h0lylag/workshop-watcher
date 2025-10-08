"""
Tests for configuration validators.

Run with: python -m unittest tests/test_validators.py -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validators import (
    validate_steam_api_key,
    validate_discord_webhook,
    validate_workshop_id,
    validate_role_id
)


class TestSteamAPIKeyValidator(unittest.TestCase):
    """Tests for validate_steam_api_key()."""
    
    def test_valid_32_char_hex_key(self):
        """Should accept valid 32-character hex string."""
        valid_key = "A1B2C3D4E5F67890A1B2C3D4E5F67890"
        self.assertTrue(validate_steam_api_key(valid_key))
    
    def test_valid_lowercase_hex(self):
        """Should accept lowercase hex characters."""
        valid_key = "a1b2c3d4e5f67890a1b2c3d4e5f67890"
        self.assertTrue(validate_steam_api_key(valid_key))
    
    def test_valid_mixed_case(self):
        """Should accept mixed case hex."""
        valid_key = "A1b2C3d4E5f67890a1B2c3D4e5F67890"
        self.assertTrue(validate_steam_api_key(valid_key))
    
    def test_invalid_too_short(self):
        """Should reject keys shorter than 32 characters."""
        short_key = "ABC123"
        self.assertFalse(validate_steam_api_key(short_key))
    
    def test_invalid_too_long(self):
        """Should reject keys longer than 32 characters."""
        long_key = "A1B2C3D4E5F67890A1B2C3D4E5F67890EXTRA"
        self.assertFalse(validate_steam_api_key(long_key))
    
    def test_invalid_non_hex_characters(self):
        """Should reject non-hexadecimal characters."""
        invalid_key = "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"  # Z is not hex
        self.assertFalse(validate_steam_api_key(invalid_key))
    
    def test_invalid_none(self):
        """Should reject None."""
        self.assertFalse(validate_steam_api_key(None))
    
    def test_invalid_empty_string(self):
        """Should reject empty string."""
        self.assertFalse(validate_steam_api_key(""))


class TestDiscordWebhookValidator(unittest.TestCase):
    """Tests for validate_discord_webhook()."""
    
    def test_valid_discord_webhook(self):
        """Should accept valid Discord webhook URL."""
        valid_url = "https://discord.com/api/webhooks/123456789/abcdefghijk"
        self.assertTrue(validate_discord_webhook(valid_url))
    
    def test_valid_discordapp_domain(self):
        """Should accept discordapp.com domain."""
        valid_url = "https://discordapp.com/api/webhooks/123/abc"
        self.assertTrue(validate_discord_webhook(valid_url))
    
    def test_invalid_wrong_domain(self):
        """Should reject non-Discord domains."""
        invalid_url = "https://example.com/api/webhooks/123/abc"
        self.assertFalse(validate_discord_webhook(invalid_url))
    
    def test_invalid_missing_api_path(self):
        """Should reject URLs without /api/webhooks/ path."""
        invalid_url = "https://discord.com/webhooks/123/abc"
        self.assertFalse(validate_discord_webhook(invalid_url))
    
    def test_invalid_http_not_https(self):
        """Should reject non-HTTPS URLs."""
        invalid_url = "http://discord.com/api/webhooks/123/abc"
        self.assertFalse(validate_discord_webhook(invalid_url))
    
    def test_invalid_none(self):
        """Should reject None."""
        self.assertFalse(validate_discord_webhook(None))
    
    def test_invalid_empty_string(self):
        """Should reject empty string."""
        self.assertFalse(validate_discord_webhook(""))


class TestWorkshopIDValidator(unittest.TestCase):
    """Tests for validate_workshop_id()."""
    
    def test_valid_positive_integer(self):
        """Should accept positive integers."""
        self.assertTrue(validate_workshop_id(123456))
    
    def test_valid_large_number(self):
        """Should accept large workshop IDs."""
        self.assertTrue(validate_workshop_id(3458840545))
    
    def test_invalid_zero(self):
        """Should reject zero."""
        self.assertFalse(validate_workshop_id(0))
    
    def test_invalid_negative(self):
        """Should reject negative numbers."""
        self.assertFalse(validate_workshop_id(-123))
    
    def test_invalid_none(self):
        """Should reject None."""
        self.assertFalse(validate_workshop_id(None))
    
    def test_valid_string_numeric(self):
        """Should accept numeric strings (auto-converts)."""
        self.assertTrue(validate_workshop_id("123456"))


class TestRoleIDValidator(unittest.TestCase):
    """Tests for validate_role_id()."""
    
    def test_valid_role_id_string(self):
        """Should accept valid Discord role ID (snowflake)."""
        valid_id = "123456789012345678"
        self.assertTrue(validate_role_id(valid_id))
    
    def test_valid_17_digit_id(self):
        """Should accept 17-digit role IDs."""
        valid_id = "12345678901234567"
        self.assertTrue(validate_role_id(valid_id))
    
    def test_valid_19_digit_id(self):
        """Should accept 19-digit role IDs."""
        valid_id = "1234567890123456789"
        self.assertTrue(validate_role_id(valid_id))
    
    def test_invalid_too_short(self):
        """Should reject IDs shorter than 17 digits."""
        short_id = "1234567890123456"
        self.assertFalse(validate_role_id(short_id))
    
    def test_invalid_too_long(self):
        """Should reject IDs longer than 19 digits."""
        long_id = "12345678901234567890"
        self.assertFalse(validate_role_id(long_id))
    
    def test_invalid_non_numeric(self):
        """Should reject non-numeric strings."""
        invalid_id = "12345678901234567a"
        self.assertFalse(validate_role_id(invalid_id))
    
    def test_valid_integer(self):
        """Should accept integers (config uses integers)."""
        self.assertTrue(validate_role_id(123456789012345678))
    
    def test_invalid_none(self):
        """Should reject None."""
        self.assertFalse(validate_role_id(None))


if __name__ == '__main__':
    unittest.main()
