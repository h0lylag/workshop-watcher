"""Validation functions for configuration."""
import re
import urllib.parse
from typing import Optional, Any


def validate_steam_api_key(key: Optional[str]) -> bool:
    """Check if Steam API key looks valid (32 hex chars)."""
    if not key:
        return False
    # Steam API keys are 32 hexadecimal characters
    return bool(re.match(r'^[A-F0-9]{32}$', key, re.IGNORECASE))


def validate_discord_webhook(url: Optional[str]) -> bool:
    """Check if Discord webhook URL looks valid (must be HTTPS)."""
    if not url:
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        # Support both discord.com and discordapp.com domains
        valid_domain = 'discord.com' in parsed.netloc or 'discordapp.com' in parsed.netloc
        return (
            parsed.scheme == 'https' and
            valid_domain and
            '/api/webhooks/' in parsed.path
        )
    except Exception:
        return False


def validate_workshop_id(id_val: Any) -> bool:
    """Check if workshop ID is valid (positive integer)."""
    try:
        id_int = int(id_val)
        return id_int > 0
    except (ValueError, TypeError):
        return False


def validate_role_id(role_id: Any) -> bool:
    """Check if Discord role ID is valid (17-19 digit integer or numeric string)."""
    try:
        rid = int(role_id)
        # Discord snowflake IDs are positive integers, typically 17-19 digits
        rid_str = str(rid)
        return rid > 0 and 17 <= len(rid_str) <= 19
    except (ValueError, TypeError):
        return False
