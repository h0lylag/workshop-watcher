import json
import os
import sys
from typing import Dict
from utils.logger import get_logger  # type: ignore


def load_modlist(path: str) -> Dict:
    """Load and validate modlist JSON file."""
    logger = get_logger()
    try:
        logger.debug(f"Loading modlist from {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        mods = data.get("mods")
        if not isinstance(mods, list) or not mods:
            raise ValueError("modlist 'mods' must be a non-empty list of objects with an 'id' field")

        valid_mods = []
        seen_ids = set()
        for i, mod in enumerate(mods):
            if not isinstance(mod, dict):
                logger.warning(f"Skipping invalid mod entry at index {i}: not a dictionary")
                continue
            if "id" not in mod:
                logger.warning(f"Skipping mod entry at index {i}: missing 'id' field")
                continue
            try:
                mod_id = int(mod["id"])
                if mod_id <= 0:
                    logger.warning(f"Skipping mod entry at index {i}: invalid ID {mod_id}")
                    continue
                if mod_id in seen_ids:
                    logger.warning(f"Duplicate mod id {mod_id} at index {i}; ignoring duplicate")
                    continue
                seen_ids.add(mod_id)
                valid_mods.append(mod)
            except (ValueError, TypeError):
                logger.warning(f"Skipping mod entry at index {i}: invalid ID format")
                continue

        if not valid_mods:
            raise ValueError("No valid mod entries found in modlist")

        data["mods"] = valid_mods
        logger.info(f"Loaded modlist with {len(valid_mods)} valid mod(s)")
        return data

    except FileNotFoundError:
        logger.error(f"Modlist file not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in modlist file {path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load modlist from {path}: {e}")
        raise


def ensure_modlist(path: str) -> None:
    """Ensure modlist file exists; create default and exit if missing."""
    logger = get_logger()

    if os.path.exists(path):
        logger.debug(f"Modlist file exists: {path}")
        return

    logger.info(f"Creating default modlist file: {path}")
    default_modlist = {
        "discord_webhook": "PUT_WEBHOOK_URL_HERE",
        "steam_api_key": "PUT_STEAM_API_KEY_HERE",
        "mods": [
            {"id": 3458840545, "alias": "Sample Mod"}
        ]
    }
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_modlist, f, indent=2)
        logger.info(
            f"Created default modlist at '{path}'. Edit it (set discord_webhook, steam_api_key, adjust mods) then re-run."
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to create default modlist '{path}': {e}")
        sys.exit(2)
