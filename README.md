# Workshop Watcher

A Steam Workshop monitoring tool that tracks mod updates and sends Discord notifications.

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

Environment variables take priority over JSON config values:

```bash
# Discord webhook URL
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."

# Steam API key
export STEAM_API_KEY="YOUR_STEAM_API_KEY_HERE"

# Ping roles (comma-separated Discord role IDs)
export PING_ROLES="1234567890123456789,9876543210987654321"
```

You can mix both methods - use JSON for defaults and env vars for overrides.

## Usage

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

## Docker/Container Usage

Environment variables are especially useful when running in containers:

```bash
docker run \
  -e DISCORD_WEBHOOK="https://discord.com/api/webhooks/..." \
  -e STEAM_API_KEY="YOUR_KEY" \
  -e PING_ROLES="123456789" \
  -v ./config:/app/config \
  workshop-watcher
```
