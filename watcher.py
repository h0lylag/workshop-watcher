import os
import sys
from typing import Dict, List, Optional
from db import connect_db, upsert_mod, get_known
from steam import fetch_published_file_details, normalize_api_item
from discord import build_embed, send_discord
from util import now_ts, chunked
from user_resolver import resolve_steam_usernames, update_mod_author_names

def poll_once(cfg: Dict, db_path: str) -> int:
    webhook = os.getenv("DISCORD_WEBHOOK_URL") or cfg.get("discord_webhook")
    if not webhook:
        print("ERROR: Discord webhook not provided (config or DISCORD_WEBHOOK_URL).", file=sys.stderr)
        return 2

    ids: List[int] = []
    alias_map: Dict[int, str] = {}
    for m in cfg["mods"]:
        mid = int(m["id"])
        ids.append(mid)
        if "alias" in m and m["alias"]:
            alias_map[mid] = str(m["alias"])

    if not ids:
        print("No mod IDs found in config.", file=sys.stderr)
        return 2

    conn = connect_db(db_path)
    details = fetch_published_file_details(ids)
    
    # Collect author IDs for Steam user resolution and process mods
    author_ids_to_resolve: List[str] = []
    mods_to_process = []  # Store mod data for later processing

    for mid in ids:
        raw = details.get(mid)
        if not raw or int(raw.get("result", 0)) != 1:
            row = {
                "id": mid,
                "title": None,
                "author_id": None,
                "author_name": None,
                "file_size": None,
                "time_created": None,
                "time_updated": None,
                "last_checked": now_ts(),
                "description": None,
                "views": None,
                "subscriptions": None,
                "favorites": None,
                "tags": None,
                "visibility": None,
                "preview_url": None,
            }
            upsert_mod(conn, row)
            continue

        norm = normalize_api_item(raw)
        known = get_known(conn, mid)
        old_updated = known[0] if known else None

        # Collect author ID for resolution
        if norm.get("author_id"):
            author_ids_to_resolve.append(norm["author_id"])

        upsert_mod(conn, norm)
        
        # Store mod info for later embed building
        mods_to_process.append({
            "mid": mid,
            "norm": norm,
            "old_updated": old_updated,
            "has_update": (old_updated is None and norm.get("time_updated")) or (old_updated and norm.get("time_updated") and norm["time_updated"] > old_updated)
        })

    # Resolve Steam usernames for all collected author IDs
    if author_ids_to_resolve:
        print(f"Resolving usernames for {len(set(author_ids_to_resolve))} unique author(s)...")
        usernames = resolve_steam_usernames(conn, list(set(author_ids_to_resolve)), cfg)
        
        # Update mod records with resolved usernames
        for mid in ids:
            raw = details.get(mid)
            if raw and int(raw.get("result", 0)) == 1:
                norm = normalize_api_item(raw)
                if norm.get("author_id") and norm["author_id"] in usernames:
                    username = usernames[norm["author_id"]]
                    if username:
                        conn.execute(
                            "UPDATE mods SET author_name = ? WHERE id = ?",
                            (username, mid)
                        )

    # Also update any existing mods that don't have author names
    updated_count = update_mod_author_names(conn, cfg)
    if updated_count > 0:
        print(f"Updated author names for {updated_count} existing mod(s).")

    # Now build embeds with resolved usernames
    updated_embeds: List[Dict] = []
    for mod_info in mods_to_process:
        if mod_info["has_update"]:
            # Get the updated mod data from database (with resolved author_name)
            cur = conn.execute(
                "SELECT id, title, author_id, author_name, file_size, time_created, time_updated, "
                "description, views, subscriptions, favorites, tags, visibility, preview_url "
                "FROM mods WHERE id = ?", 
                (mod_info["mid"],)
            )
            row = cur.fetchone()
            if row:
                # Convert database row to dict
                mod_data = {
                    "id": row[0],
                    "title": row[1],
                    "author_id": row[2],
                    "author_name": row[3],
                    "file_size": row[4],
                    "time_created": row[5],
                    "time_updated": row[6],
                    "description": row[7],
                    "views": row[8],
                    "subscriptions": row[9],
                    "favorites": row[10],
                    "tags": row[11],
                    "visibility": row[12],
                    "preview_url": row[13],
                }
                updated_embeds.append(build_embed(mod_data, alias_map, mod_info["old_updated"]))

    conn.commit()
    conn.close()

    if updated_embeds:
        successes = 0
        for chunk in chunked(updated_embeds, 10):
            chunk_size = len(chunk)
            content_msg = f"Workshop mod updated" if chunk_size == 1 else f"Workshop mods updated"
            if send_discord(
                webhook,
                content=content_msg,
                embeds=chunk,
            ):
                successes += len(chunk)
        if successes:
            print(f"Notified {successes} update(s).")
        else:
            print("Failed to send updates (see errors above).")
    else:
        print("No updates.")

    return 0
