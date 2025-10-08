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
    """Check if Discord webhook URL looks valid."""
    if not url:
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        return (
            parsed.scheme in ('http', 'https') and
            'discord.com' in parsed.netloc and
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
    """Check if Discord role ID is valid (positive integer, typically 17-19 digits)."""
    try:
        rid = int(role_id)
        # Discord snowflake IDs are positive integers, typically 17-19 digits
        return rid > 0 and len(str(rid)) >= 17
    except (ValueError, TypeError):
        return False
