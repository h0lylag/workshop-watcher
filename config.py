import json
import os
import sys
from typing import Dict
from logger import get_logger

def load_config(path: str) -> Dict:
    """Load and validate configuration from JSON file."""
    logger = get_logger()
    
    try:
        logger.debug(f"Loading config from {path}")
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            
        # Validate config structure
        if not isinstance(cfg.get("mods"), list) or not cfg["mods"]:
            raise ValueError("config 'mods' must be a non-empty list of objects with an 'id' field.")
        
        # Validate mod entries
        valid_mods = []
        for i, mod in enumerate(cfg["mods"]):
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
                valid_mods.append(mod)
            except (ValueError, TypeError):
                logger.warning(f"Skipping mod entry at index {i}: invalid ID format")
                continue
        
        if not valid_mods:
            raise ValueError("No valid mod entries found in config")
        
        cfg["mods"] = valid_mods
        logger.info(f"Loaded config with {len(valid_mods)} valid mod(s)")
        return cfg
        
    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file {path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load config from {path}: {e}")
        raise

def ensure_config(path: str) -> None:
    """Ensure config file exists, create default if missing."""
    logger = get_logger()
    
    if os.path.exists(path):
        logger.debug(f"Config file exists: {path}")
        return
        
    logger.info(f"Creating default config file: {path}")
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
        logger.info(f"Created default config at '{path}'. Edit it (set discord_webhook, steam_api_key, adjust mods) then re-run.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to create default config '{path}': {e}")
        sys.exit(2)
