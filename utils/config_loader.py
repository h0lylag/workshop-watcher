import json
import logging
import os
import sys
from typing import Dict

logger = logging.getLogger("config_loader")


def load_config(path: str) -> dict:
    """Loads a JSON config file from the given path."""
    if not os.path.exists(path):
        logger.error(f"Config file not found at '{path}'")
        return {}

    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.exception(f"Failed to decode config at '{path}'")
            return {}


def ensure_config(path: str) -> None:
    """Ensure config file exists; create default and exit if missing."""
    if os.path.exists(path):
        logger.debug(f"Config file exists: {path}")
        return

    logger.info(f"Creating default config file: {path}")
    default_config = {
        "discord_webhook": "PUT_WEBHOOK_URL_HERE",
        "steam_api_key": "PUT_STEAM_API_KEY_HERE",
        "ping_roles": [123456789012345678]
    }
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"Created default config at '{path}'. Edit it to set your webhook and API key, then re-run.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to create default config '{path}': {e}")
        sys.exit(2)


def load_modlist(path: str) -> Dict:
    """Load and validate modlist JSON file."""
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
    if os.path.exists(path):
        logger.debug(f"Modlist file exists: {path}")
        return

    logger.info(f"Creating default modlist file: {path}")
    default_modlist = {"mods": [{"id": 3458840545, "alias": "Sample Mod"}]}
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_modlist, f, indent=2)
        logger.info(f"Created default modlist at '{path}'. Edit it to add your mods then re-run.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to create default modlist '{path}': {e}")
        sys.exit(2)
