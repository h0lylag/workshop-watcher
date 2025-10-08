import json
import urllib.parse
import urllib.request
from typing import Dict, List, Optional
from utils.helpers import chunked, now_ts
from utils.logger import get_logger
from utils.constants import STEAM_WORKSHOP_BATCH_SIZE, STEAM_USER_BATCH_SIZE, STEAM_API_TIMEOUT

STEAM_API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
STEAM_USER_API_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
WORKSHOP_ITEM_URL = "https://steamcommunity.com/sharedfiles/filedetails/?id={id}"
WORKSHOP_CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog/{id}"

def fetch_published_file_details(ids: List[int]) -> Dict[int, Dict]:
    """Fetch published file details from Steam Workshop API."""
    logger = get_logger()
    logger.debug(f"Fetching details for {len(ids)} mod(s)")
    
    results: Dict[int, Dict] = {}
    for batch in chunked(ids, STEAM_WORKSHOP_BATCH_SIZE):
        try:
            logger.debug(f"Processing batch of {len(batch)} mod(s)")
            data = {"itemcount": len(batch)}
            for i, mid in enumerate(batch):
                data[f"publishedfileids[{i}]"] = str(mid)
            encoded = urllib.parse.urlencode(data).encode("utf-8")
            req = urllib.request.Request(STEAM_API_URL, method="POST")
            
            with urllib.request.urlopen(req, data=encoded, timeout=STEAM_API_TIMEOUT) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                
            details = payload.get("response", {}).get("publishedfiledetails", [])
            logger.debug(f"Received {len(details)} detail record(s) from Steam API")
            
            for d in details:
                try:
                    pid = int(d.get("publishedfileid"))
                    result_code = int(d.get("result", 0))
                    if result_code == 1:
                        results[pid] = d
                        logger.debug(f"Successfully got details for mod {pid}")
                    else:
                        logger.warning(f"Steam API returned result code {result_code} for mod {pid}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid publishedfileid in Steam API response: {d.get('publishedfileid')}. Error: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to fetch Steam API data for batch: {e}", exc_info=True)
            # Continue with next batch even if one fails
            continue
            
    logger.info(f"Successfully fetched details for {len(results)} out of {len(ids)} mod(s)")
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
    logger = get_logger()
    
    if not api_key:
        logger.warning("No Steam API key provided for user summaries")
        return {}
    
    if not steam_ids:
        logger.debug("No Steam IDs provided for user summaries")
        return {}
    
    logger.debug(f"Fetching user summaries for {len(steam_ids)} Steam ID(s)")
    results: Dict[str, Dict] = {}
    
    # Steam API allows up to 100 Steam IDs per request
    for batch in chunked(steam_ids, STEAM_USER_BATCH_SIZE):
        try:
            logger.debug(f"Processing user batch of {len(batch)} Steam ID(s)")
            steam_ids_str = ",".join(batch)
            params = {
                "key": api_key,
                "steamids": steam_ids_str,
                "format": "json"
            }
            
            url = f"{STEAM_USER_API_URL}?{urllib.parse.urlencode(params)}"
            
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=STEAM_API_TIMEOUT) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                
            players = payload.get("response", {}).get("players", [])
            logger.debug(f"Received {len(players)} player record(s) from Steam API")
            
            for player in players:
                steam_id = player.get("steamid")
                if steam_id:
                    results[steam_id] = player
                    logger.debug(f"Got user data for Steam ID {steam_id}")
                    
        except Exception as e:
            logger.error(f"Failed to fetch Steam user data for batch: {e}", exc_info=True)
            # Continue processing other batches even if one fails
            continue
            
    logger.info(f"Successfully fetched user data for {len(results)} out of {len(steam_ids)} Steam ID(s)")
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
