from config import ensure_config, load_config  # type: ignore
from watcher import poll_once  # type: ignore
from db import connect_db  # type: ignore
from user_resolver import update_mod_author_names  # type: ignore

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
    return ap.parse_args()


def main():
    args = parse_args()
    ensure_config(args.config)
    try:
        cfg = load_config(args.config)
    except Exception as e:
        print(f"Failed to load config: {e}", file=sys.stderr)
        sys.exit(2)

    if not cfg.get("discord_webhook") and not os.getenv("DISCORD_WEBHOOK_URL") and not args.update_authors:
        print("Warning: No webhook in config and DISCORD_WEBHOOK_URL not set; will fail to notify.", file=sys.stderr)

    # Handle --update-authors option
    if args.update_authors:
        api_key = cfg.get("steam_api_key") or os.getenv("STEAM_API_KEY")
        if not api_key or api_key == "PUT_STEAM_API_KEY_HERE":
            print("Error: Steam API key required for updating author names. Set steam_api_key in config or STEAM_API_KEY environment variable.", file=sys.stderr)
            print("Get your Steam API key at: https://steamcommunity.com/dev/apikey", file=sys.stderr)
            sys.exit(1)
        
        conn = connect_db(args.db)
        updated_count = update_mod_author_names(conn, cfg)
        conn.close()
        print(f"Updated author names for {updated_count} mod(s).")
        sys.exit(0)

    if args.watch and args.watch > 0:
        while True:
            try:
                poll_once(cfg, args.db)
            except Exception as e:
                print(f"Polling error: {e}", file=sys.stderr)
            time.sleep(args.watch)
    else:
        rc = poll_once(cfg, args.db)
        sys.exit(rc)

if __name__ == "__main__":
    main()
