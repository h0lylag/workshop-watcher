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

        workshop_items = data.get("workshop_items")
        if not isinstance(workshop_items, list) or not workshop_items:
            raise ValueError("modlist 'workshop_items' must be a non-empty list of objects with an 'id' field")

        valid_items = []
        seen_ids = set()
        for i, item in enumerate(workshop_items):
            if not isinstance(item, dict):
                logger.warning(f"Skipping invalid workshop item at index {i}: not a dictionary")
                continue
            if "id" not in item:
                logger.warning(f"Skipping workshop item at index {i}: missing 'id' field")
                continue
            try:
                item_id = int(item["id"])
                if item_id <= 0:
                    logger.warning(f"Skipping workshop item at index {i}: invalid ID {item_id}")
                    continue
                if item_id in seen_ids:
                    logger.warning(f"Duplicate workshop item id {item_id} at index {i}; ignoring duplicate")
                    continue
                seen_ids.add(item_id)
                valid_items.append(item)
            except (ValueError, TypeError):
                logger.warning(f"Skipping workshop item at index {i}: invalid ID format")
                continue

        if not valid_items:
            raise ValueError("No valid workshop items found in modlist")

        data["workshop_items"] = valid_items
        logger.info(f"Loaded modlist with {len(valid_items)} valid workshop item(s)")
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
    default_modlist = {"workshop_items": [{"id": 3458840545, "name": "Sample Mod"}]}
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_modlist, f, indent=2)
        logger.info(f"Created default modlist at '{path}'. Edit it to add your mods then re-run.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to create default modlist '{path}': {e}")
        sys.exit(2)
