"""
Tests for configuration validators.

Run with: pytest tests/test_validators.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validators import (
    validate_steam_api_key,
    validate_discord_webhook,
    validate_workshop_id,
    validate_role_id
)


class TestSteamAPIKeyValidator:
    """Tests for validate_steam_api_key()."""
    
    def test_valid_32_char_hex_key(self):
        """Should accept valid 32-character hex string."""
        valid_key = "A1B2C3D4E5F67890A1B2C3D4E5F67890"
        assert validate_steam_api_key(valid_key) is True
    
    def test_valid_lowercase_hex(self):
        """Should accept lowercase hex characters."""
        valid_key = "a1b2c3d4e5f67890a1b2c3d4e5f67890"
        assert validate_steam_api_key(valid_key) is True
    
    def test_valid_mixed_case(self):
        """Should accept mixed case hex."""
        valid_key = "A1b2C3d4E5f67890a1B2c3D4e5F67890"
        assert validate_steam_api_key(valid_key) is True
    
    def test_invalid_too_short(self):
        """Should reject keys shorter than 32 characters."""
        short_key = "ABC123"
        assert validate_steam_api_key(short_key) is False
    
    def test_invalid_too_long(self):
        """Should reject keys longer than 32 characters."""
        long_key = "A1B2C3D4E5F67890A1B2C3D4E5F67890EXTRA"
        assert validate_steam_api_key(long_key) is False
    
    def test_invalid_non_hex_characters(self):
        """Should reject non-hexadecimal characters."""
        invalid_key = "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"  # Z is not hex
        assert validate_steam_api_key(invalid_key) is False
    
    def test_invalid_none(self):
        """Should reject None."""
        assert validate_steam_api_key(None) is False
    
    def test_invalid_empty_string(self):
        """Should reject empty string."""
        assert validate_steam_api_key("") is False


class TestDiscordWebhookValidator:
    """Tests for validate_discord_webhook()."""
    
    def test_valid_discord_webhook(self):
        """Should accept valid Discord webhook URL."""
        valid_url = "https://discord.com/api/webhooks/123456789/abcdefghijk"
        assert validate_discord_webhook(valid_url) is True
    
    def test_valid_discordapp_domain(self):
        """Should accept discordapp.com domain."""
        valid_url = "https://discordapp.com/api/webhooks/123/abc"
        assert validate_discord_webhook(valid_url) is True
    
    def test_invalid_wrong_domain(self):
        """Should reject non-Discord domains."""
        invalid_url = "https://example.com/api/webhooks/123/abc"
        assert validate_discord_webhook(invalid_url) is False
    
    def test_invalid_missing_api_path(self):
        """Should reject URLs without /api/webhooks/ path."""
        invalid_url = "https://discord.com/webhooks/123/abc"
        assert validate_discord_webhook(invalid_url) is False
    
    def test_invalid_http_not_https(self):
        """Should reject non-HTTPS URLs."""
        invalid_url = "http://discord.com/api/webhooks/123/abc"
        assert validate_discord_webhook(invalid_url) is False
    
    def test_invalid_none(self):
        """Should reject None."""
        assert validate_discord_webhook(None) is False
    
    def test_invalid_empty_string(self):
        """Should reject empty string."""
        assert validate_discord_webhook("") is False


class TestWorkshopIDValidator:
    """Tests for validate_workshop_id()."""
    
    def test_valid_positive_integer(self):
        """Should accept positive integers."""
        assert validate_workshop_id(123456) is True
    
    def test_valid_large_number(self):
        """Should accept large workshop IDs."""
        assert validate_workshop_id(3458840545) is True
    
    def test_invalid_zero(self):
        """Should reject zero."""
        assert validate_workshop_id(0) is False
    
    def test_invalid_negative(self):
        """Should reject negative numbers."""
        assert validate_workshop_id(-123) is False
    
    def test_invalid_none(self):
        """Should reject None."""
        assert validate_workshop_id(None) is False
    
    def test_invalid_string(self):
        """Should reject string (even if numeric)."""
        assert validate_workshop_id("123456") is False


class TestRoleIDValidator:
    """Tests for validate_role_id()."""
    
    def test_valid_role_id_string(self):
        """Should accept valid Discord role ID (snowflake)."""
        valid_id = "123456789012345678"
        assert validate_role_id(valid_id) is True
    
    def test_valid_17_digit_id(self):
        """Should accept 17-digit role IDs."""
        valid_id = "12345678901234567"
        assert validate_role_id(valid_id) is True
    
    def test_valid_19_digit_id(self):
        """Should accept 19-digit role IDs."""
        valid_id = "1234567890123456789"
        assert validate_role_id(valid_id) is True
    
    def test_invalid_too_short(self):
        """Should reject IDs shorter than 17 digits."""
        short_id = "1234567890123456"
        assert validate_role_id(short_id) is False
    
    def test_invalid_too_long(self):
        """Should reject IDs longer than 19 digits."""
        long_id = "12345678901234567890"
        assert validate_role_id(long_id) is False
    
    def test_invalid_non_numeric(self):
        """Should reject non-numeric strings."""
        invalid_id = "12345678901234567a"
        assert validate_role_id(invalid_id) is False
    
    def test_invalid_integer(self):
        """Should reject integers (must be string)."""
        assert validate_role_id(123456789012345678) is False
    
    def test_invalid_none(self):
        """Should reject None."""
        assert validate_role_id(None) is False


# Run with: pytest tests/test_validators.py -v
# or: pytest tests/test_validators.py -v --tb=short  (shorter error traces)
