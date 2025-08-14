"""Discord utilities (renamed from discord_util)."""
import json
import sys
import datetime as dt
import urllib.request
import time
from urllib.error import HTTPError, URLError
from typing import Dict, List, Optional
from steam import WORKSHOP_ITEM_URL, WORKSHOP_CHANGELOG_URL

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

def send_discord(webhook: str, content: str, embeds: Optional[List[Dict]] = None, max_retries: int = 5) -> bool:
    """Send a Discord webhook with rate limit handling and exponential backoff retry."""
    body = {"content": content}
    if embeds:
        body["embeds"] = embeds
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
            with urllib.request.urlopen(req, timeout=30) as resp:
                _ = resp.read()
            return True
            
        except HTTPError as e:
            if e.code == 429:  # Rate limited
                try:
                    # Try to get rate limit info from headers
                    retry_after = e.headers.get('Retry-After')
                    if retry_after:
                        retry_delay = float(retry_after)
                        print(f"Discord rate limited. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
                    else:
                        # Exponential backoff if no Retry-After header
                        retry_delay = min(2 ** attempt, 60)  # Cap at 60 seconds
                        print(f"Discord rate limited (no retry-after header). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
                    
                    time.sleep(retry_delay)
                    continue  # Retry the request
                    
                except (ValueError, TypeError):
                    # Fallback to exponential backoff if Retry-After header is invalid
                    retry_delay = min(2 ** attempt, 60)
                    print(f"Discord rate limited (invalid retry-after header). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
                    time.sleep(retry_delay)
                    continue
                    
            elif e.code >= 500:  # Server errors - retry with exponential backoff
                retry_delay = min(2 ** attempt, 30)  # Cap at 30 seconds for server errors
                print(f"Discord server error {e.code}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
                time.sleep(retry_delay)
                continue
                
            else:  # Client errors (400, 401, 403, etc.) - don't retry
                try:
                    err_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    err_body = "<no body>"
                print(f"Discord webhook HTTP error {e.code}: {e.reason} body={err_body[:300]}", file=sys.stderr)
                return False
                
        except URLError as e:
            # Network/connection errors - retry with exponential backoff
            retry_delay = min(2 ** attempt, 30)
            print(f"Discord webhook connection error: {e.reason}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
            time.sleep(retry_delay)
            continue
            
        except Exception as e:
            # Unexpected errors - retry with exponential backoff
            retry_delay = min(2 ** attempt, 30)
            print(f"Discord webhook unexpected error: {e}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...", file=sys.stderr)
            time.sleep(retry_delay)
            continue
    
    print(f"Discord webhook failed after {max_retries} attempts", file=sys.stderr)
    return False

def build_embed(entry: Dict, alias_map: Dict[int, str], old_updated: Optional[int]) -> Dict:
    mid = entry["id"]
    alias = alias_map.get(mid)
    title = entry.get("title") or f"Workshop Item {mid}"
    
    # Limit title length to prevent embed size issues
    if len(title) > 100:
        title = title[:100] + "..."
    
    display_title = f"{title} · ({alias})" if alias and alias != title else title
    updated = entry.get("time_updated")
    created = entry.get("time_created")
    filesize = entry.get("file_size")
    author_name = entry.get("author_name")
    author_id = entry.get("author_id")
    preview_url = entry.get("preview_url")
    
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
        {"name": "Changelog", "value": f"[View changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/{mid})", "inline": True},
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

    # Truncate description to 200 characters with ellipsis if needed
    description = entry.get("description") or ""
    if len(description) > 200:
        description = description[:200] + "..."

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
    
    return embed
