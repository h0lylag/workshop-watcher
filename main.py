from config import ensure_config, load_config  # type: ignore
from watcher import poll_once  # type: ignore
from db import connect_db  # type: ignore
from user_resolver import update_mod_author_names  # type: ignore
from logger import setup_logging, get_logger  # type: ignore

import argparse
import os
import sys
import time


def parse_args():
    ap = argparse.ArgumentParser(description="Monitor Steam Workshop mods and notify Discord of updates.")
    ap.add_argument("--config", default="config.json", help="Path to config.json (default: config.json; created if missing)")
    ap.add_argument("--db", default="mods.db", help="Path to SQLite database (default: mods.db)")
    ap.add_argument("--watch", type=int, help="Interval seconds to poll repeatedly (omit to run once)")
    ap.add_argument("--update-authors", action="store_true", help="Update author names for existing mods and exit")
    ap.add_argument("--dry-run", action="store_true", help="Poll and build embeds but do not send Discord webhooks")
    ap.add_argument("--log-file", default="workshop-watcher.log", help="Path to log file (default: workshop-watcher.log)")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level (default: INFO)")
    ap.add_argument("--no-console", action="store_true", help="Disable console output (log to file only)")
    return ap.parse_args()


def main():
    args = parse_args()
    
    # Setup logging first
    logger = setup_logging(
        log_file=args.log_file,
        log_level=args.log_level,
        console_output=not args.no_console
    )
    
    logger.info("Workshop Watcher starting up")
    logger.debug(f"Arguments: {vars(args)}")
    
    ensure_config(args.config)
    try:
        cfg = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")
        logger.debug(f"Monitoring {len(cfg.get('mods', []))} mod(s)")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(2)

    if not cfg.get("discord_webhook") and not os.getenv("DISCORD_WEBHOOK_URL") and not args.update_authors:
        logger.warning("No webhook in config and DISCORD_WEBHOOK_URL not set; will fail to notify")

    # Handle --update-authors option
    if args.update_authors:
        logger.info("Running in author update mode")
        api_key = cfg.get("steam_api_key") or os.getenv("STEAM_API_KEY")
        if not api_key or api_key == "PUT_STEAM_API_KEY_HERE":
            logger.error("Steam API key required for updating author names. Set steam_api_key in config or STEAM_API_KEY environment variable.")
            logger.info("Get your Steam API key at: https://steamcommunity.com/dev/apikey")
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
        logger.info(f"Starting watch mode with {args.watch} second intervals (dry-run={'yes' if args.dry_run else 'no'})")
        try:
            while True:
                try:
                    poll_once(cfg, args.db, dry_run=args.dry_run)
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
        logger.info(f"Running single poll (dry-run={'yes' if args.dry_run else 'no'})")
        try:
            rc = poll_once(cfg, args.db, dry_run=args.dry_run)
            logger.info("Single poll completed successfully")
            sys.exit(rc)
        except Exception as e:
            logger.error(f"Single poll failed: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    main()
