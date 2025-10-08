# Workshop Watcher 

A (Vibe-Coded) Steam Workshop monitoring tool that tracks mod updates and sends Discord notifications.

## How It Works

1. Queries the Steam API to check when workshop items were last updated
2. Compares update times against a local SQLite database
3. Sends Discord webhook notifications when mods are updated
4. Caches Steam user information to display mod author names

Perfect for DayZ server admins or any game that uses Steam Workshop!

## Requirements

- Python 3.6 or newer
- No external dependencies! Uses only Python standard library

## Setup

1. Get a Steam API key from [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. Set up a Discord webhook in your server
3. Run once to generate config files: `python3 main.py`
4. Edit `config/config.json` with your webhook URL, API key, and ping roles
5. Edit `config/modlist.json` with your workshop item IDs

## Configuration

### Option 1: JSON Config Files (Recommended for persistence)

Edit `config/config.json`:
```json
{
  "discord_webhook": "https://discord.com/api/webhooks/...",
  "steam_api_key": "YOUR_STEAM_API_KEY_HERE",
  "ping_roles": [1234567890123456789]
}
```

Edit `config/modlist.json`:
```json
{
  "workshop_items": [
    {
      "id": 1234567890,
      "name": "My Favorite Mod"
    }
  ]
}
```

### Option 2: Environment Variables (Override JSON values)

Environment variables take priority over JSON config values and command-line defaults:

#### Configuration Overrides
```bash
# Discord webhook URL
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."

# Steam API key
export STEAM_API_KEY="YOUR_STEAM_API_KEY_HERE"

# Ping roles (comma-separated Discord role IDs)
export PING_ROLES="1234567890123456789,9876543210987654321"
```

#### File Path Overrides
```bash
# Override where config/database files are stored (useful for NixOS/containers)
export CONFIG_PATH="/var/lib/workshop-watcher/config/config.json"
export MODLIST_PATH="/var/lib/workshop-watcher/config/modlist.json"
export DB_PATH="/var/lib/workshop-watcher/db/mods.db"
```

You can mix both methods - use JSON for defaults and env vars for overrides.

## Usage

### Basic Commands

```bash
# Check once and exit
python3 main.py

# Monitor continuously (check every 300 seconds)
python3 main.py --watch 300

# Update author names for existing mods
python3 main.py --update-authors

# Show stored mod update timestamps
python3 main.py --show-updates
```

### Advanced Options

```bash
# Control logging verbosity
python3 main.py --log-level DEBUG   # Show detailed debug info
python3 main.py --log-level WARNING # Only show warnings/errors

# Override file paths via command-line
python3 main.py --config /path/to/config.json \
                --modlist /path/to/modlist.json \
                --db /path/to/database.db

# Combine options
python3 main.py --watch 600 --log-level WARNING
```

## Docker/Container/NixOS Usage

Environment variables are especially useful when running in containers or NixOS:

```bash
docker run \
  -e DISCORD_WEBHOOK="https://discord.com/api/webhooks/..." \
  -e STEAM_API_KEY="YOUR_KEY" \
  -e PING_ROLES="123456789" \
  -e CONFIG_PATH="/data/config.json" \
  -e MODLIST_PATH="/data/modlist.json" \
  -e DB_PATH="/data/mods.db" \
  -v ./data:/data \
  workshop-watcher
```

This approach ensures your database and config persist outside the container/Nix store.

## What Gets Notified?

When a mod updates, Discord receives:
- 🔔 Mod name and Steam Workshop link
- 👤 Author name (cached from Steam)
- 🕒 Update timestamp
- 🔗 Direct link to the workshop page
- 📌 Ping roles (if configured)

## Development

### Running Tests

The project includes a comprehensive test suite with **56 tests** and zero external dependencies:

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_validators -v

# Quick demo (no framework required)
python tests/simple_test_demo.py
```

See [`tests/README.md`](tests/README.md) for more details.

### Test Coverage

- ✅ Configuration validators
- ✅ Database operations  
- ✅ Utility functions
- ✅ SQLite isolation (temporary test databases)

Tests run in under 0.4 seconds and have caught real security bugs!

## Troubleshooting

### "Invalid Steam API key"
- Ensure your API key is 32 hexadecimal characters
- Get a new key at https://steamcommunity.com/dev/apikey

### "Invalid Discord webhook"
- Webhook URL must start with `https://` (HTTP not allowed for security)
- Must contain `/api/webhooks/` in the path
- Both `discord.com` and `discordapp.com` domains are supported

### "No updates detected" (but you know mods updated)
- Run `python3 main.py --show-updates` to see stored timestamps
- Delete `db/mods.db` to reset and redetect all mods as new
- Check `--log-level DEBUG` for detailed API responses

### First run shows all mods as "updated"
- This is normal! The database is empty on first run
- All tracked mods will be added to the database
- Subsequent runs will only notify about actual updates

## File Structure

```
workshop-watcher/
├── main.py              # Entry point
├── config/
│   ├── config.json      # API keys, webhook, roles
│   └── modlist.json     # Workshop items to track
├── db/
│   └── mods.db         # SQLite database (auto-created)
├── utils/
│   ├── config_loader.py # Configuration management
│   ├── discord.py       # Discord webhook sender
│   ├── helpers.py       # Utility functions
│   └── validators.py    # Input validation
├── db/
│   └── db.py           # Database operations
└── tests/
    ├── test_*.py       # Unit tests
    └── README.md       # Testing documentation
```

## License

This project is open source. Feel free to use and modify as needed!

````
