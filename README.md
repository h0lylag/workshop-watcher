# Workshop Watcher

A Steam Workshop monitoring tool that tracks mod updates and sends Discord notifications.

## Setup

1. Get a Steam API key from [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. Set up a Discord webhook in your server
3. Run once to generate modlist file: `python3 main.py`
4. Edit `modlist.json` with your webhook URL, API key, and mod IDs

## Usage

```bash
# Check once and exit
python3 main.py

# Monitor continuously (check every 300 seconds)
python3 main.py --watch 300
```

## Modlist Format

Edit `modlist.json`:
```json
{
  "discord_webhook": "https://discord.com/api/webhooks/...",
  "steam_api_key": "YOUR_STEAM_API_KEY_HERE",
  "mods": [
    {
      "id": 1234567890,
      "alias": "My Favorite Mod"
    }
  ]
}
```
