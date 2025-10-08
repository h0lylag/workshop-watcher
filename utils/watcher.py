import os
import sys
from typing import Dict, List, Optional
from db.db import connect_db, upsert_mod, get_known, get_mod_by_id
from utils.steam import fetch_published_file_details, normalize_api_item
from utils.discord import build_embed, send_discord
from utils.helpers import now_ts, chunked, create_empty_mod_record
from utils.user_resolver import resolve_steam_usernames, update_mod_author_names, USER_CACHE_DURATION
from utils.logger import get_logger
from utils.constants import DISCORD_MAX_EMBEDS_PER_MESSAGE

def poll_once(cfg: Dict, db_path: str) -> int:
    """Poll Steam Workshop once for mod updates."""
    logger = get_logger()
    logger.info("Starting polling cycle")

    webhook = cfg.get("discord_webhook")
    if not webhook:
        logger.error("Discord webhook not provided in config or DISCORD_WEBHOOK environment variable")
        return 2

    # Extract ping_roles for notifications
    ping_roles = cfg.get("ping_roles", [])

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
        logger.error("No valid mod IDs found in config")
        return 2

    logger.info(f"Monitoring {len(ids)} mod(s)")
    
    try:
        conn = connect_db(db_path)
    except Exception as e:
        logger.error(f"Failed to connect to database {db_path}: {e}")
        return 2
    
    try:
        logger.debug("Fetching mod details from Steam API")
        details = fetch_published_file_details(ids)
        logger.debug(f"Received details for {len(details)} mod(s)")
        # Cache normalized items so we don't recompute
        normalized_cache: Dict[int, Dict] = {}

        # Collect author IDs for Steam user resolution and process mods
        author_ids_to_resolve: List[str] = []
        mods_to_process = []  # Store mod data for later processing

        for mid in ids:
            raw = details.get(mid)
            if not raw or int(raw.get("result", 0)) != 1:
                logger.warning(f"No valid data for mod {mid} from Steam API")
                upsert_mod(conn, create_empty_mod_record(mid))
                continue

            norm = normalize_api_item(raw)
            normalized_cache[mid] = norm
            known = get_known(conn, mid)
            old_updated = known[0] if known else None

            # Collect author ID for resolution
            if norm.get("author_id"):
                author_ids_to_resolve.append(norm["author_id"])

            upsert_mod(conn, norm)
            
            # Store mod info for later embed building
            has_update = (old_updated is None and norm.get("time_updated")) or (old_updated and norm.get("time_updated") and norm["time_updated"] > old_updated)
            if has_update:
                logger.info(f"Detected {'new' if old_updated is None else 'updated'} mod: {norm.get('title', mid)}")
            
            mods_to_process.append({
                "mid": mid,
                "norm": norm,
                "old_updated": old_updated,
                "has_update": has_update
            })

        # Resolve Steam usernames for all collected author IDs
        if author_ids_to_resolve:
            unique_authors = list(set(author_ids_to_resolve))
            logger.info(f"Resolving usernames for {len(unique_authors)} unique author(s)")
            # New log: show how many are cached vs need fetch
            try:
                current_time = now_ts()
                if unique_authors:
                    placeholders = ",".join(["?"] * len(unique_authors))
                    cur_chk = conn.execute(
                        f"SELECT steam_id, last_fetched, fetch_failed, persona_name FROM steam_users WHERE steam_id IN ({placeholders})",
                        unique_authors
                    )
                    cache_hits = 0
                    to_query = set(unique_authors)
                    for row in cur_chk.fetchall():
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
            try:
                usernames = resolve_steam_usernames(conn, unique_authors, cfg)
                for mid in ids:
                    if mid in normalized_cache:
                        norm = normalized_cache[mid]
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

        # Now build embeds with resolved usernames
        new_embeds: List[Dict] = []
        updated_embeds: List[Dict] = []
        
        for mod_info in mods_to_process:
            if mod_info["has_update"]:
                try:
                    mod_data = get_mod_by_id(conn, mod_info["mid"])
                    if mod_data:
                        embed = build_embed(mod_data, alias_map, mod_info["old_updated"])
                        if mod_info["old_updated"] is None:
                            new_embeds.append(embed)
                        else:
                            updated_embeds.append(embed)
                except Exception as e:
                    logger.error(f"Failed to build embed for mod {mod_info['mid']}: {e}", exc_info=True)

        conn.commit()
        conn.close()

        total_notifications = 0
        
        # Send notifications for new mods
        if new_embeds:
            logger.info(f"Preparing notifications for {len(new_embeds)} new mod(s)")
            successes = 0
            for chunk in chunked(new_embeds, DISCORD_MAX_EMBEDS_PER_MESSAGE):
                chunk_size = len(chunk)
                content_msg = "Workshop mod added" if chunk_size == 1 else "Workshop mods added"
                if send_discord(webhook, content=content_msg, embeds=chunk, ping_roles=ping_roles):
                    successes += len(chunk)
                else:
                    logger.error(f"Failed to send {chunk_size} new mod notification(s)")
            if successes:
                logger.info(f"Successfully notified {successes} new mod(s)")
                total_notifications += successes

        # Send notifications for updated mods
        if updated_embeds:
            logger.info(f"Preparing notifications for {len(updated_embeds)} updated mod(s)")
            successes = 0
            for chunk in chunked(updated_embeds, DISCORD_MAX_EMBEDS_PER_MESSAGE):
                chunk_size = len(chunk)
                content_msg = "Workshop mod updated" if chunk_size == 1 else "Workshop mods updated"
                if send_discord(webhook, content=content_msg, embeds=chunk, ping_roles=ping_roles):
                    successes += len(chunk)
                else:
                    logger.error(f"Failed to send {chunk_size} update notification(s)")
            if successes:
                logger.info(f"Successfully notified {successes} update(s)")
                total_notifications += successes

        if total_notifications == 0:
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
