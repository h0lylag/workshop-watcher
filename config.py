import json
import os
import sys
from typing import Dict

def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if not isinstance(cfg.get("mods"), list) or not cfg["mods"]:
        raise ValueError("config 'mods' must be a non-empty list of objects with an 'id' field.")
    return cfg

def ensure_config(path: str) -> None:
    if os.path.exists(path):
        return
    default_cfg = {
        "discord_webhook": "PUT_WEBHOOK_URL_HERE",
        "steam_api_key": "PUT_STEAM_API_KEY_HERE",
        "mods": [
            {"id": 3458840545, "alias": "Sample Mod"}
        ]
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_cfg, f, indent=2)
        print(f"Created default config at '{path}'. Edit it (set discord_webhook, steam_api_key, adjust mods) then re-run.")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to create default config '{path}': {e}", file=sys.stderr)
        sys.exit(2)
