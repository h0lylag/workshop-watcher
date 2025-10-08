"""Steam user resolution and caching module."""
import os
import sqlite3
from typing import Dict, List, Optional, Set, Any
from db.db import get_steam_user, upsert_steam_user, mark_steam_user_fetch_failed
from utils.steam import fetch_steam_user_summaries, normalize_steam_user
from utils.helpers import now_ts
from utils.logger import get_logger
from utils.constants import USER_CACHE_TTL_SECONDS

# Cache user data for 7 days
USER_CACHE_DURATION = USER_CACHE_TTL_SECONDS

# Module-level logger
logger = get_logger()

def resolve_steam_usernames(conn: sqlite3.Connection, steam_ids: List[str], cfg: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Resolve Steam IDs to usernames, using cached data when available.
    
    Args:
        conn: Database connection
        steam_ids: List of Steam IDs to resolve
        cfg: Configuration dictionary (should contain steam_api_key)
        
    Returns:
        Dict mapping Steam ID to username (or None if resolution failed)
    """
    if not steam_ids:
        logger.debug("No Steam IDs provided for resolution")
        return {}
    
    logger.debug(f"Resolving usernames for {len(steam_ids)} Steam ID(s)")
    
    # Get Steam API key from config (which may have been overridden by environment variable)
    api_key = cfg.get("steam_api_key")
    if not api_key:
        logger.warning("No Steam API key found in config.json or STEAM_API_KEY environment variable")
        return {steam_id: None for steam_id in steam_ids}
    
    results: Dict[str, Optional[str]] = {}
    ids_to_fetch: Set[str] = set()
    current_time = now_ts()
    
    # Check cache for each Steam ID
    for steam_id in steam_ids:
        try:
            cached_user = get_steam_user(conn, steam_id)
            
            if cached_user:
                persona_name, real_name, profile_url, avatar_url, last_fetched, fetch_failed = cached_user
                
                # Check if cache is still valid
                if (current_time - last_fetched) < USER_CACHE_DURATION:
                    if fetch_failed:
                        # Previous fetch failed and cache is still valid, don't retry
                        logger.debug(f"Using cached failed fetch for Steam ID {steam_id}")
                        results[steam_id] = None
                    else:
                        # Use cached username
                        logger.debug(f"Using cached username for Steam ID {steam_id}: {persona_name}")
                        results[steam_id] = persona_name
                else:
                    # Cache expired, need to refetch
                    logger.debug(f"Cache expired for Steam ID {steam_id}, will refetch")
                    ids_to_fetch.add(steam_id)
            else:
                # No cache entry, need to fetch
                logger.debug(f"No cache entry for Steam ID {steam_id}, will fetch")
                ids_to_fetch.add(steam_id)
                
        except Exception as e:
            logger.error(f"Error checking cache for Steam ID {steam_id}: {e}")
            ids_to_fetch.add(steam_id)
    
    # Fetch user data for IDs not in cache or with expired cache
    if ids_to_fetch:
        logger.info(f"Fetching user data for {len(ids_to_fetch)} Steam ID(s)")
        try:
            user_summaries = fetch_steam_user_summaries(list(ids_to_fetch), api_key)
            
            for steam_id in ids_to_fetch:
                if steam_id in user_summaries:
                    # Successfully fetched user data
                    user_data = normalize_steam_user(user_summaries[steam_id])
                    upsert_steam_user(conn, user_data)
                    results[steam_id] = user_data["persona_name"]
                    logger.debug(f"Resolved Steam ID {steam_id} to username: {user_data['persona_name']}")
                else:
                    # Failed to fetch user data
                    logger.warning(f"Failed to fetch user data for Steam ID {steam_id}")
                    mark_steam_user_fetch_failed(conn, steam_id)
                    results[steam_id] = None
                    
            # Commit the database changes
            conn.commit()
            logger.debug("Committed user data changes to database")
            
        except Exception as e:
            logger.error(f"Error fetching Steam user data: {e}", exc_info=True)
            # Mark all failed fetches
            for steam_id in ids_to_fetch:
                mark_steam_user_fetch_failed(conn, steam_id)
                results[steam_id] = None
            conn.commit()
    
    successful_resolutions = sum(1 for v in results.values() if v is not None)
    logger.info(f"Successfully resolved {successful_resolutions} out of {len(steam_ids)} Steam ID(s)")
    
    return results

def update_mod_author_names(conn: sqlite3.Connection, cfg: Dict[str, Any]) -> int:
    """
    Update author names for all mods in the database that have author_id but no author_name.
    
    Args:
        conn: Database connection
        cfg: Configuration dictionary
        
    Returns:
        Number of author names updated
    """
    # Get all mods with author_id but no author_name
    cur = conn.execute(
        "SELECT DISTINCT author_id FROM mods WHERE author_id IS NOT NULL AND (author_name IS NULL OR author_name = '')"
    )
    steam_ids = [row[0] for row in cur.fetchall()]
    
    if not steam_ids:
        return 0
    
    # Resolve usernames
    usernames = resolve_steam_usernames(conn, steam_ids, cfg)
    
    # Update mod records with resolved usernames
    updated_count = 0
    for steam_id, username in usernames.items():
        if username:
            c = conn.execute(
                "UPDATE mods SET author_name = ? WHERE author_id = ? AND (author_name IS NULL OR author_name = '')",
                (username, steam_id)
            )
            # Use cursor rowcount correctly
            if c.rowcount > 0:
                updated_count += c.rowcount
    
    conn.commit()
    return updated_count
