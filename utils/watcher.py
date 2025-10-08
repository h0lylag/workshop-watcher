import os
import sys
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import sqlite3
from db.db import connect_db, upsert_mod, get_last_update_time, get_mod_by_id, get_cached_steam_users
from utils.steam import fetch_published_file_details, normalize_api_item
from utils.discord import build_embed, send_discord
from utils.helpers import get_current_timestamp, chunk_list, create_empty_mod_record
from utils.user_resolver import resolve_steam_usernames, update_mod_author_names, USER_CACHE_DURATION
from utils.logger import get_logger
from utils.constants import DISCORD_MAX_EMBEDS_PER_MESSAGE


@dataclass
class WorkshopItems:
    """Parsed workshop items with IDs and aliases."""
    ids: List[int]
    alias_map: Dict[int, str]


@dataclass
class ModUpdate:
    """Information about a mod update."""
    mod_id: int
    old_updated: Optional[int]
    is_new: bool


def _validate_poll_config(cfg: Dict[str, Any]) -> bool:
    """Validate polling configuration has required fields."""
    logger = get_logger()
    webhook = cfg.get("discord_webhook")
    if not webhook:
        logger.error(
            "Discord webhook required. Set it in one of these ways:\n"
            "  1. Add 'discord_webhook' to config/config.json\n"
            "  2. Set DISCORD_WEBHOOK environment variable\n"
            "  3. Create webhook: Server Settings -> Integrations -> Webhooks -> New Webhook"
        )
        return False
    return True


def _parse_workshop_items(cfg: Dict[str, Any]) -> Optional[WorkshopItems]:
    """Parse workshop items from configuration."""
    logger = get_logger()
    ids: List[int] = []
    alias_map: Dict[int, str] = {}
    
    for item in cfg["workshop_items"]:
        try:
            mid = int(item["id"])
            ids.append(mid)
            if "name" in item and item["name"]:
                alias_map[mid] = str(item["name"])
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Invalid workshop item entry in config: {item}. Error: {e}")
            continue
    
    if not ids:
        logger.error(
            "No valid mod IDs found in modlist. Check that:\n"
            "  1. config/modlist.json exists and has 'workshop_items' array\n"
            "  2. Each item has a valid numeric 'id' field\n"
            "  3. Example: {\"workshop_items\": [{\"id\": 3458840545, \"name\": \"My Mod\"}]}"
        )
        return None
    
    logger.info(f"Monitoring {len(ids)} mod(s)")
    return WorkshopItems(ids=ids, alias_map=alias_map)


def _fetch_and_process_mods(
    conn: sqlite3.Connection,
    workshop_items: WorkshopItems
) -> Tuple[List[ModUpdate], Dict[int, Dict[str, Any]], List[str]]:
    """
    Fetch mod details from Steam and process them.
    
    Returns:
        Tuple of (mod_updates, normalized_cache, author_ids_to_resolve)
    """
    logger = get_logger()
    logger.debug("Fetching mod details from Steam API")
    
    details = fetch_published_file_details(workshop_items.ids)
    logger.debug(f"Received details for {len(details)} mod(s)")
    
    normalized_cache: Dict[int, Dict[str, Any]] = {}
    author_ids_to_resolve: List[str] = []
    mod_updates: List[ModUpdate] = []
    
    for mid in workshop_items.ids:
        raw = details.get(mid)
        if not raw or int(raw.get("result", 0)) != 1:
            logger.warning(f"No valid data for mod {mid} from Steam API")
            upsert_mod(conn, create_empty_mod_record(mid))
            continue
        
        norm = normalize_api_item(raw)
        normalized_cache[mid] = norm
        old_updated = get_last_update_time(conn, mid)
        
        # Collect author ID for resolution
        if norm.get("author_id"):
            author_ids_to_resolve.append(norm["author_id"])
        
        upsert_mod(conn, norm)
        
        # Detect if this is an update
        has_update = (
            (old_updated is None and norm.get("time_updated")) or 
            (old_updated and norm.get("time_updated") and norm["time_updated"] > old_updated)
        )
        
        if has_update:
            is_new = old_updated is None
            logger.info(f"Detected {'new' if is_new else 'updated'} mod: {norm.get('title', mid)}")
            mod_updates.append(ModUpdate(
                mod_id=mid,
                old_updated=old_updated,
                is_new=is_new
            ))
    
    return mod_updates, normalized_cache, author_ids_to_resolve


def _resolve_author_names(
    conn: sqlite3.Connection,
    author_ids: List[str],
    normalized_cache: Dict[int, Dict[str, Any]],
    cfg: Dict[str, Any]
) -> None:
    """Resolve Steam usernames for mod authors and update database."""
    if not author_ids:
        return
    
    logger = get_logger()
    unique_authors = list(set(author_ids))
    logger.info(f"Resolving usernames for {len(unique_authors)} unique author(s)")
    
    # Show cache hit statistics
    try:
        current_time = get_current_timestamp()
        if unique_authors:
            cached_users = get_cached_steam_users(conn, unique_authors)
            cache_hits = 0
            to_query = set(unique_authors)
            
            for row in cached_users:
                steam_id = row[0]
                last_fetched = row[1]
                fetch_failed = row[2]
                persona_name = row[3]
                if (
                    persona_name
                    and not fetch_failed
                    and isinstance(last_fetched, int)
                    and (current_time - last_fetched) < USER_CACHE_DURATION
                ):
                    cache_hits += 1
                    if steam_id in to_query:
                        to_query.discard(steam_id)
            logger.info(
                f"Author cache hits: {cache_hits} / {len(unique_authors)}; querying {len(to_query)}"
            )
    except Exception as e:
        logger.debug(f"Author cache inspection failed: {e}")
    
    # Resolve usernames
    try:
        usernames = resolve_steam_usernames(conn, unique_authors, cfg)
        for mid, norm in normalized_cache.items():
            if norm.get("author_id") and norm["author_id"] in usernames and usernames[norm["author_id"]]:
                conn.execute(
                    "UPDATE mods SET author_name = ? WHERE id = ?",
                    (usernames[norm["author_id"]], mid)
                )
                logger.debug(f"Updated author name for mod {mid}: {usernames[norm['author_id']]}")
    except Exception as e:
        logger.error(f"Failed to resolve Steam usernames: {e}", exc_info=True)
    
    # Also update any existing mods that don't have author names
    try:
        updated_count = update_mod_author_names(conn, cfg)
        if updated_count > 0:
            logger.info(f"Updated author names for {updated_count} existing mod(s)")
    except Exception as e:
        logger.error(f"Failed to update existing author names: {e}", exc_info=True)


def _build_notification_embeds(
    conn: sqlite3.Connection,
    mod_updates: List[ModUpdate],
    alias_map: Dict[int, str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Build Discord embeds for new and updated mods."""
    logger = get_logger()
    new_embeds = []
    updated_embeds = []
    
    for update in mod_updates:
        try:
            mod = dict(conn.execute("SELECT * FROM mods WHERE id = ?", (update.mod_id,)).fetchone())
        except Exception as e:
            logger.error(f"Failed to fetch mod {update.mod_id} for embed: {e}")
            continue
        
        embed = build_embed(mod, alias_map, update.old_updated)
        display_name = alias_map.get(update.mod_id, mod.get("name", "Unknown"))
        
        if update.is_new:
            new_embeds.append(embed)
            logger.info(f"New mod detected: {display_name} (ID: {update.mod_id})")
        else:
            updated_embeds.append(embed)
            logger.info(f"Update detected for: {display_name} (ID: {update.mod_id})")
    
    return new_embeds, updated_embeds


def _send_notifications(
    webhook: str,
    new_embeds: List[Dict[str, Any]],
    updated_embeds: List[Dict[str, Any]],
    ping_roles: Optional[List[str]]
) -> int:
    """Send Discord notifications for new and updated mods."""
    logger = get_logger()
    total_sent = 0
    
    # Send new mod notifications
    if new_embeds:
        logger.info(f"Sending {len(new_embeds)} new mod notification(s)")
        for embed_batch in chunk_list(new_embeds, DISCORD_MAX_EMBEDS_PER_MESSAGE):
            content = None
            if ping_roles:
                content = " ".join([f"<@&{rid}>" for rid in ping_roles])
            
            success = send_discord(
                webhook,
                embeds=embed_batch,
                content=content
            )
            if success:
                total_sent += len(embed_batch)
            else:
                logger.error(f"Failed to send batch of {len(embed_batch)} new mod notification(s)")
    
    # Send updated mod notifications
    if updated_embeds:
        logger.info(f"Sending {len(updated_embeds)} mod update notification(s)")
        for embed_batch in chunk_list(updated_embeds, DISCORD_MAX_EMBEDS_PER_MESSAGE):
            success = send_discord(
                webhook,
                embeds=embed_batch,
                content=None
            )
            if success:
                total_sent += len(embed_batch)
            else:
                logger.error(f"Failed to send batch of {len(embed_batch)} update notification(s)")
    
    return total_sent


def poll_once(cfg: Dict, db_path: str) -> int:
    """
    Poll Steam Workshop once for mod updates and send Discord notifications.
    
    Orchestrates the complete polling workflow:
    1. Validate configuration
    2. Parse workshop items
    3. Connect to database
    4. Fetch and process mods from Steam
    5. Resolve author usernames
    6. Build Discord embeds
    7. Send notifications
    
    Returns:
        0 on success, 1 on critical error, 2 on configuration error
    """
    logger = get_logger()
    logger.info("Starting polling cycle")
    
    # Step 1: Validate configuration
    if not _validate_poll_config(cfg):
        return 2
    
    # Step 2: Parse workshop items
    workshop_items = _parse_workshop_items(cfg)
    if not workshop_items:
        return 2
    
    logger.info(f"Monitoring {len(workshop_items.ids)} mod(s)")
    
    # Step 3: Connect to database
    try:
        conn = connect_db(db_path)
    except Exception as e:
        logger.error(
            f"Failed to connect to database at {db_path}: {e}\n"
            "  Check that:\n"
            "  1. The directory exists and is writable\n"
            "  2. You have permission to create/access the database file\n"
            "  3. The path is correct (use --db option or DB_PATH env var to change)"
        )
        return 2
    
    try:
        # Step 4: Fetch and process mods from Steam
        mod_updates, normalized_cache, author_ids = _fetch_and_process_mods(conn, workshop_items)
        
        # Step 5: Resolve author usernames
        _resolve_author_names(conn, author_ids, normalized_cache, cfg)
        
        # Step 6: Build Discord embeds
        new_embeds, updated_embeds = _build_notification_embeds(conn, mod_updates, workshop_items.alias_map)
        
        # Commit all database changes
        conn.commit()
        conn.close()
        
        # Step 7: Send notifications
        webhook = cfg["discord_webhook"]
        ping_roles = cfg.get("ping_roles")
        total_sent = _send_notifications(webhook, new_embeds, updated_embeds, ping_roles)
        
        if total_sent == 0:
            logger.info("No updates detected")
        
        logger.info("Polling cycle completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Critical error during polling: {e}", exc_info=True)
        try:
            conn.close()
        except Exception:
            logger.debug("Failed to close database connection during cleanup")
        return 1
