from utils.config_loader import ensure_modlist, load_modlist, load_config  # type: ignore
from utils.watcher import poll_once  # type: ignore
from db.db import connect_db  # type: ignore
from utils.user_resolver import update_mod_author_names  # type: ignore
from utils.logger import setup_logging, get_logger  # type: ignore
from utils.validators import validate_steam_api_key, validate_discord_webhook, validate_workshop_id, validate_role_id

import argparse
import os
import sys
import time
from datetime import datetime, UTC


def parse_args():
    ap = argparse.ArgumentParser(description="Monitor Steam Workshop mods and notify Discord of updates.")
    
    # Allow environment variable overrides for file paths
    default_config = os.getenv("CONFIG_PATH", "config/config.json")
    default_modlist = os.getenv("MODLIST_PATH", "config/modlist.json")
    default_db = os.getenv("DB_PATH", "db/mods.db")
    
    ap.add_argument("--config", default=default_config, help=f"Path to config JSON (default: {default_config}, env: CONFIG_PATH)")
    ap.add_argument("--modlist", default=default_modlist, help=f"Path to modlist JSON (default: {default_modlist}, env: MODLIST_PATH)")
    ap.add_argument("--db", default=default_db, help=f"Path to SQLite database (default: {default_db}, env: DB_PATH)")
    ap.add_argument("--watch", type=int, help="Interval seconds to poll repeatedly (omit to run once)")
    ap.add_argument("--update-authors", action="store_true", help="Update author names for existing mods and exit")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level (default: INFO)")
    ap.add_argument("--show-updates", action="store_true", help="List mods with their stored last update timestamps and exit")
    return ap.parse_args()


def main():
    args = parse_args()

    logger = setup_logging(log_level=args.log_level)

    logger.info("Workshop Watcher starting up")
    logger.debug(f"Arguments: {vars(args)}")

    # Ensure modlist JSON exists (uses ensure_modlist for creation logic)
    ensure_modlist(args.modlist)
    try:
        base_cfg = load_config(args.config)
        modlist_cfg = load_modlist(args.modlist)
        cfg = base_cfg.copy()
        cfg.update(modlist_cfg)
        logger.info(f"Loaded config from {args.config}")
        logger.info(f"Loaded modlist from {args.modlist}")
        logger.debug(f"Monitoring {len(cfg.get('workshop_items', []))} workshop item(s)")
    except Exception as e:
        logger.error(
            f"Failed to load configuration: {e}\n"
            "  Check that:\n"
            "  1. Config file exists at {args.config} (or set CONFIG_PATH env var)\n"
            "  2. Modlist file exists at {args.modlist} (or set MODLIST_PATH env var)\n"
            "  3. Both files contain valid JSON\n"
            "  4. Files are readable"
        )
        sys.exit(2)

    # Validate configuration
    webhook = cfg.get("discord_webhook")
    if webhook and not validate_discord_webhook(webhook):
        logger.error(
            f"Invalid Discord webhook URL format: {webhook[:50]}...\n"
            "  Expected format: https://discord.com/api/webhooks/..."
        )
        sys.exit(2)
    
    api_key = cfg.get("steam_api_key")
    if api_key and api_key != "PUT_STEAM_API_KEY_HERE" and not validate_steam_api_key(api_key):
        logger.warning(
            f"Steam API key doesn't match expected format (32 hexadecimal characters)\n"
            "  Your key: {api_key[:8]}... (length: {len(api_key)})\n"
            "  This may cause issues with Steam API requests"
        )
    
    # Validate workshop item IDs
    workshop_items = cfg.get("workshop_items", [])
    invalid_ids = []
    for item in workshop_items:
        if not validate_workshop_id(item.get("id")):
            invalid_ids.append(item.get("id"))
    
    if invalid_ids:
        logger.error(
            f"Invalid workshop item IDs found: {invalid_ids}\n"
            "  Workshop IDs must be positive integers"
        )
        sys.exit(2)
    
    # Validate ping role IDs
    ping_roles = cfg.get("ping_roles", [])
    if ping_roles:
        invalid_roles = [rid for rid in ping_roles if not validate_role_id(rid)]
        if invalid_roles:
            logger.warning(
                f"Invalid Discord role IDs found: {invalid_roles}\n"
                "  Role IDs should be positive integers (typically 17-19 digits)\n"
                "  These will be ignored in notifications"
            )
            # Filter out invalid role IDs
            cfg["ping_roles"] = [rid for rid in ping_roles if validate_role_id(rid)]

    logger.info("Configuration validated successfully")

    # New quick command: show updates and exit
    if getattr(args, "show_updates", False):
        try:
            conn = connect_db(args.db)
            cur = conn.execute("SELECT id, title, time_updated, last_checked FROM mods ORDER BY time_updated DESC NULLS LAST")
            rows = cur.fetchall()
            if not rows:
                print("No mods stored in database.")
            else:
                print(f"Stored mods (count={len(rows)}):")
                for r in rows:
                    tu = r["time_updated"]
                    lc = r["last_checked"]
                    tu_h = datetime.fromtimestamp(tu, UTC).isoformat().replace('+00:00', 'Z') if isinstance(tu, int) and tu > 0 else "-"
                    lc_h = datetime.fromtimestamp(lc, UTC).isoformat().replace('+00:00', 'Z') if isinstance(lc, int) and lc > 0 else "-"
                    print(f"{r['id']:>12}  updated={tu_h:<25}  last_checked={lc_h:<25}  title={r['title'] or ''}")
            conn.close()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Failed listing updates: {e}")
            sys.exit(1)

    if not cfg.get("discord_webhook") and not args.update_authors:
        logger.warning("No webhook in config or DISCORD_WEBHOOK environment variable; will fail to notify")

    if args.update_authors:
        logger.info("Running in author update mode")
        api_key = cfg.get("steam_api_key")
        if not api_key or api_key == "PUT_STEAM_API_KEY_HERE":
            logger.error(
                "Steam API key required for updating author names. Set it in one of these ways:\n"
                "  1. Add 'steam_api_key' to config/config.json\n"
                "  2. Set STEAM_API_KEY environment variable\n"
                "  3. Get a key at: https://steamcommunity.com/dev/apikey"
            )
            sys.exit(1)
        try:
            conn = connect_db(args.db)
            updated_count = update_mod_author_names(conn, cfg)
            conn.close()
            logger.info(f"Updated author names for {updated_count} mod(s)")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Failed to update author names: {e}", exc_info=True)
            sys.exit(1)

    if args.watch and args.watch > 0:
        logger.info(f"Starting watch mode with {args.watch} second intervals")
        try:
            while True:
                try:
                    poll_once(cfg, args.db)
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, stopping after current cycle")
                    break
                except Exception as e:
                    logger.error(f"Polling error: {e}", exc_info=True)
                logger.debug(f"Sleeping for {args.watch} seconds")
                try:
                    time.sleep(args.watch)
                except KeyboardInterrupt:
                    logger.info("Interrupted during sleep, exiting cleanly")
                    break
        except KeyboardInterrupt:
            logger.info("Shutdown requested, exiting")
    else:
        logger.info("Running single poll")
        try:
            rc = poll_once(cfg, args.db)
            logger.info("Single poll completed successfully")
            sys.exit(rc)
        except Exception as e:
            logger.error(f"Single poll failed: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    main()
