from utils.config_loader import ensure_modlist, load_modlist, load_config  # type: ignore
from utils.watcher import poll_once  # type: ignore
from db.db import connect_db  # type: ignore
from utils.user_resolver import update_mod_author_names  # type: ignore
from utils.logger import setup_logging, get_logger  # type: ignore

import argparse
import os
import sys
import time
from datetime import datetime, UTC


def parse_args():
    ap = argparse.ArgumentParser(description="Monitor Steam Workshop mods and notify Discord of updates.")
    ap.add_argument("--config", default="config/config.json", help="Path to config JSON (default: config/config.json)")
    ap.add_argument("--modlist", default="config/modlist.json", help="Path to modlist JSON (default: config/modlist.json; created if missing)")
    ap.add_argument("--db", default="db/mods.db", help="Path to SQLite database (default: db/mods.db)")
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
        cfg = load_config(args.config)
        modlist = load_modlist(args.modlist)
        cfg.update(modlist)
        logger.info(f"Loaded config from {args.config}")
        logger.info(f"Loaded modlist from {args.modlist}")
        logger.debug(f"Monitoring {len(cfg.get('mods', []))} mod(s)")
    except Exception as e:
        logger.error(f"Failed to load config or modlist: {e}")
        sys.exit(2)

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

    if not cfg.get("discord_webhook") and not os.getenv("DISCORD_WEBHOOK_URL") and not args.update_authors:
        logger.warning("No webhook in config and DISCORD_WEBHOOK_URL not set; will fail to notify")

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
