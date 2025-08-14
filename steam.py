import json
import urllib.parse
import urllib.request
from typing import Dict, List, Optional
from util import chunked
from util import now_ts

STEAM_API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
STEAM_USER_API_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
WORKSHOP_ITEM_URL = "https://steamcommunity.com/sharedfiles/filedetails/?id={id}"

def fetch_published_file_details(ids: List[int]) -> Dict[int, Dict]:
    results: Dict[int, Dict] = {}
    for batch in chunked(ids, 50):
        data = {"itemcount": len(batch)}
        for i, mid in enumerate(batch):
            data[f"publishedfileids[{i}]"] = str(mid)
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(STEAM_API_URL, method="POST")
        with urllib.request.urlopen(req, data=encoded, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        for d in payload.get("response", {}).get("publishedfiledetails", []):
            try:
                pid = int(d.get("publishedfileid"))
            except Exception:
                continue
            results[pid] = d
    return results

def normalize_api_item(raw: Dict) -> Dict:
    id_int = int(raw.get("publishedfileid"))
    
    # Parse tags if available
    tags_list = []
    if "tags" in raw and isinstance(raw["tags"], list):
        for tag in raw["tags"]:
            if isinstance(tag, dict) and "tag" in tag:
                tags_list.append(tag["tag"])
    tags_str = ",".join(tags_list) if tags_list else None
    
    return {
        "id": id_int,
        "title": raw.get("title"),
        "author_id": str(raw.get("creator")) if raw.get("creator") is not None else None,
        "author_name": None,  # Steam API doesn't provide creator name, would need separate API call
        "file_size": raw.get("file_size"),
        "time_created": raw.get("time_created"),
        "time_updated": raw.get("time_updated"),
        "last_checked": now_ts(),
        "description": raw.get("description"),
        "views": raw.get("views"),
        "subscriptions": raw.get("subscriptions"),
        "favorites": raw.get("favorited"),
        "tags": tags_str,
        "visibility": raw.get("visibility"),
        "preview_url": raw.get("preview_url"),
    }

def fetch_steam_user_summaries(steam_ids: List[str], api_key: str) -> Dict[str, Dict]:
    """Fetch Steam user summaries using Steam Web API."""
    if not api_key:
        return {}
    
    results: Dict[str, Dict] = {}
    
    # Steam API allows up to 100 Steam IDs per request
    for batch in chunked(steam_ids, 100):
        steam_ids_str = ",".join(batch)
        params = {
            "key": api_key,
            "steamids": steam_ids_str,
            "format": "json"
        }
        
        url = f"{STEAM_USER_API_URL}?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                
            players = payload.get("response", {}).get("players", [])
            for player in players:
                steam_id = player.get("steamid")
                if steam_id:
                    results[steam_id] = player
                    
        except Exception as e:
            print(f"Failed to fetch Steam user data: {e}")
            # Continue processing other batches even if one fails
            
    return results

def normalize_steam_user(raw: Dict) -> Dict:
    """Normalize Steam user data from API response."""
    return {
        "steam_id": raw.get("steamid"),
        "persona_name": raw.get("personaname"),
        "real_name": raw.get("realname"),
        "profile_url": raw.get("profileurl"),
        "avatar_url": raw.get("avatarfull"),
        "last_fetched": now_ts(),
        "fetch_failed": 0,
    }
