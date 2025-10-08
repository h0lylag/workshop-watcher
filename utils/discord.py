"""Discord utilities (renamed from discord_util)."""

import json
import sys
import datetime as dt
import urllib.request
import time
from urllib.error import HTTPError, URLError
from typing import Dict, List, Optional
from utils.steam import WORKSHOP_ITEM_URL, WORKSHOP_CHANGELOG_URL
from utils.logger import get_logger
from utils.config_loader import load_config
from utils.constants import (
    DISCORD_EMBED_TITLE_MAX_DISPLAY,
    DISCORD_EMBED_DESC_MAX_DISPLAY,
    DISCORD_EMBED_MAX_SIZE,
    DISCORD_EMBED_HARD_LIMIT,
    MAX_DISCORD_RETRIES,
    MAX_RETRY_DELAY_SECONDS,
    SERVER_ERROR_RETRY_DELAY_SECONDS,
)
import builtins

# Module-level logger
logger = get_logger()

def ts_to_discord(ts: int) -> str:
    return f"<t:{ts}:R>"

def human_size(n: Optional[object]) -> str:
    if n is None:
        return "n/a"
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if n < 1024:
            if unit == "B":
                return f"{n} {unit}"
            else:
                return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} EB"

def send_discord(webhook: str, content: str, embeds: Optional[List[Dict]] = None, max_retries: int = MAX_DISCORD_RETRIES, ping_roles: Optional[List[int]] = None) -> bool:
    """Send a Discord webhook with rate limit handling and exponential backoff retry. Optionally pings roles."""

    if not webhook:
        logger.error("Discord webhook URL is empty")
        return False

    if not webhook.startswith(('http://', 'https://')):
        logger.error(f"Invalid Discord webhook URL format: {webhook[:50]}...")
        return False

    # Load ping roles from global config if not provided
    if ping_roles is None:
        try:
            config = getattr(builtins, 'global_config', {})
            ping_roles = config.get("ping_roles", [])
        except Exception as e:
            logger.warning(f"Could not load ping_roles from global_config: {e}")
            ping_roles = []

    # Build role mention string
    role_mentions = " ".join([f"<@&{rid}>" for rid in ping_roles]) if ping_roles else ""
    if role_mentions:
        if content:
            content = f"{role_mentions} {content}"
        else:
            content = role_mentions

    body = {"content": content}
    if embeds:
        body["embeds"] = embeds
        logger.debug(f"Sending Discord message with {len(embeds)} embed(s)")
    else:
        logger.debug("Sending Discord message without embeds")

    data = json.dumps(body).encode("utf-8")

    for attempt in range(max_retries):
        req = urllib.request.Request(
            webhook,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "workshop-watcher/1.0 (+https://github.com/h0lylag) Python"
            }
        )

        try:
            logger.debug(f"Attempting Discord webhook (attempt {attempt + 1}/{max_retries})")
            with urllib.request.urlopen(req, timeout=30) as resp:
                _ = resp.read()
            logger.info("Discord webhook sent successfully")
            return True

        except HTTPError as e:
            if e.code == 429:  # Rate limited
                try:
                    # Try to get rate limit info from headers
                    retry_after = e.headers.get('Retry-After')
                    if retry_after:
                        retry_delay = float(retry_after)
                        logger.warning(f"Discord rate limited. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
                    else:
                        # Exponential backoff if no Retry-After header
                        retry_delay = min(2 ** attempt, MAX_RETRY_DELAY_SECONDS)
                        logger.warning(f"Discord rate limited (no retry-after header). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")

                    time.sleep(retry_delay)
                    continue  # Retry the request

                except (ValueError, TypeError):
                    # Fallback to exponential backoff if Retry-After header is invalid
                    retry_delay = min(2 ** attempt, MAX_RETRY_DELAY_SECONDS)
                    logger.warning(f"Discord rate limited (invalid retry-after header). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                    continue

            elif e.code >= 500:  # Server errors - retry with exponential backoff
                retry_delay = min(2 ** attempt, SERVER_ERROR_RETRY_DELAY_SECONDS)
                logger.warning(f"Discord server error {e.code}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
                continue

            else:  # Client errors (400, 401, 403, etc.) - don't retry
                try:
                    err_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    err_body = "<no body>"
                logger.error(f"Discord webhook HTTP error {e.code}: {e.reason} body={err_body[:300]}")
                return False

        except URLError as e:
            # Network/connection errors - retry with exponential backoff
            retry_delay = min(2 ** attempt, SERVER_ERROR_RETRY_DELAY_SECONDS)
            logger.warning(f"Discord webhook connection error: {e.reason}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
            time.sleep(retry_delay)
            continue

        except Exception as e:
            # Unexpected errors - retry with exponential backoff
            retry_delay = min(2 ** attempt, SERVER_ERROR_RETRY_DELAY_SECONDS)
            logger.warning(f"Discord webhook unexpected error: {e}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
            time.sleep(retry_delay)
            continue

    logger.error(f"Discord webhook failed after {max_retries} attempts")
    return False

def build_embed(entry: Dict, alias_map: Dict[int, str], old_updated: Optional[int]) -> Dict:
    """Build a Discord embed for a workshop mod."""
    
    try:
        mid = entry["id"]
        alias = alias_map.get(mid)
        title = entry.get("title") or f"Workshop Item {mid}"
        
        # Limit title length to prevent embed size issues
        if len(title) > DISCORD_EMBED_TITLE_MAX_DISPLAY:
            title = title[:DISCORD_EMBED_TITLE_MAX_DISPLAY] + "..."
            logger.debug(f"Truncated long title for mod {mid}")
        
        display_title = f"{title} · ({alias})" if alias and alias != title else title
        updated = entry.get("time_updated")
        created = entry.get("time_created")
        filesize = entry.get("file_size")
        author_name = entry.get("author_name")
        author_id = entry.get("author_id")
        preview_url = entry.get("preview_url")
        
        logger.debug(f"Building embed for mod {mid}: {title}")
        
        # Create author display - prefer name with profile link, fallback to profile link only, then unknown
        if author_name and author_id:
            author_display = f"[{author_name}](https://steamcommunity.com/profiles/{author_id})"
        elif author_name:
            author_display = author_name
        elif author_id:
            author_display = f"[{author_id}](https://steamcommunity.com/profiles/{author_id})"
        else:
            author_display = "Unknown"
        
        # Additional stats
        views = entry.get("views")
        subscriptions = entry.get("subscriptions")
        favorites = entry.get("favorites")
        tags = entry.get("tags")

        fields = [
            {"name": "Updated", "value": ts_to_discord(updated) if updated else "n/a", "inline": True},
            {"name": "Created", "value": ts_to_discord(created) if created else "n/a", "inline": True},
            {"name": "File size", "value": human_size(filesize), "inline": True},
            {"name": "Changelog", "value": f"[View changelog]({WORKSHOP_CHANGELOG_URL.format(id=mid)})", "inline": True},
        ]
        
        # Add stats if available
        if views is not None or subscriptions is not None or favorites is not None:
            stats_value = []
            if views is not None:
                stats_value.append(f"{views:,} views")
            if subscriptions is not None:
                stats_value.append(f"{subscriptions:,} subs")
            if favorites is not None:
                stats_value.append(f"{favorites:,} favs")
            if stats_value:
                fields.append({"name": "Stats", "value": " • ".join(stats_value), "inline": True})
        
        # Add author field
        fields.append({"name": "Creator", "value": author_display, "inline": True})
        
        if old_updated and updated and updated != old_updated:
            fields.append({"name": "Prev. update", "value": ts_to_discord(old_updated), "inline": True})

        # Create footer text with creator ID if available
        footer_text = f"Workshop ID: {mid}"
        if author_id:
            footer_text += f" • Creator ID: {author_id}"

        # Truncate description to configured max length with word boundary
        description = entry.get("description") or ""
        if len(description) > DISCORD_EMBED_DESC_MAX_DISPLAY:
            truncated = description[:DISCORD_EMBED_DESC_MAX_DISPLAY]
            # ensure we cut at last whitespace if possible
            cut = truncated.rfind(" ")
            # Only cut at word boundary if we have one in the last 25% of the text
            word_boundary_threshold = int(DISCORD_EMBED_DESC_MAX_DISPLAY * 0.75)
            if cut > word_boundary_threshold:
                truncated = truncated[:cut]
            description = truncated + "..."
            logger.debug(f"Truncated long description for mod {mid}")

        embed = {
            "title": display_title,
            "url": WORKSHOP_ITEM_URL.format(id=mid),
            "description": description,
            "color": 0x2ecc71,
            "fields": fields,
            "footer": {"text": footer_text},
        }
        
        # Add image if preview URL is available
        if preview_url:
            embed["image"] = {"url": preview_url}
        
        # Calculate approximate embed size for debugging
        embed_size = len(json.dumps(embed))
        if embed_size > DISCORD_EMBED_MAX_SIZE:
            logger.warning(f"Large embed for mod {mid}: {embed_size} characters (approaching Discord's {DISCORD_EMBED_HARD_LIMIT} char limit)")
        else:
            logger.debug(f"Embed for mod {mid}: {embed_size} characters")
        
        return embed
        
    except Exception as e:
        logger.error(f"Failed to build embed for mod {entry.get('id', 'unknown')}: {e}", exc_info=True)
        return {
            "title": f"Workshop Item {entry.get('id', 'unknown')}",
            "description": "Error building embed",
            "color": 0xe74c3c,
            "footer": {"text": f"Workshop ID: {entry.get('id', 'unknown')}"}
        }
