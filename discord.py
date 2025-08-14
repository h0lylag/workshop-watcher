"""Discord utilities (renamed from discord_util)."""
import json
import sys
import datetime as dt
import urllib.request
from urllib.error import HTTPError, URLError
from typing import Dict, List, Optional
from steam import WORKSHOP_ITEM_URL

def ts_to_discord(ts: int) -> str:
    return f"<t:{ts}:F> (<t:{ts}:R>)"

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

def send_discord(webhook: str, content: str, embeds: Optional[List[Dict]] = None) -> bool:
    body = {"content": content}
    if embeds:
        body["embeds"] = embeds
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "workshop-watcher/1.0 (+https://github.com/h0lylag) Python"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            _ = resp.read()
        return True
    except HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = "<no body>"
        print(f"Discord webhook HTTP error {e.code}: {e.reason} body={err_body[:300]}", file=sys.stderr)
    except URLError as e:
        print(f"Discord webhook connection error: {e.reason}", file=sys.stderr)
    except Exception as e:
        print(f"Discord webhook unexpected error: {e}", file=sys.stderr)
    return False

def build_embed(entry: Dict, alias_map: Dict[int, str], old_updated: Optional[int]) -> Dict:
    mid = entry["id"]
    alias = alias_map.get(mid)
    title = entry.get("title") or f"Workshop Item {mid}"
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

    embed = {
        "title": display_title,
        "url": WORKSHOP_ITEM_URL.format(id=mid),
        "description": (entry.get("description") or "")[:3000],
        "color": 0x2ecc71,
        "fields": fields,
        "footer": {"text": footer_text},
    }
    
    # Add image if preview URL is available
    if preview_url:
        embed["image"] = {"url": preview_url}
    
    return embed
