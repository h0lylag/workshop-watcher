# Workshop Watcher

A Python tool for monitoring Steam Workshop mods and sending Discord notifications when they're updated.

## Features

- Monitor multiple Steam Workshop mods for updates
- Send Discord webhook notifications when mods are updated
- Cache mod information in SQLite database
- Resolve Steam user IDs to usernames using Steam Web API
- Detailed Discord embeds with mod information, stats, and author names

## Setup

### 1. Configuration

Create or edit `config.json`:

```json
{
  "discord_webhook": "YOUR_DISCORD_WEBHOOK_URL",
  "steam_api_key": "YOUR_STEAM_API_KEY",
  "mods": [
    {
      "id": 3458840545,
      "alias": "Rip It Energy Drinks"
    }
  ]
}
```

### 2. Discord Webhook

1. In your Discord server, go to Server Settings → Integrations → Webhooks
2. Create a new webhook or copy an existing one
3. Copy the webhook URL and add it to your config

### 3. Steam API Key (Optional but Recommended)

To resolve Steam user IDs to usernames:

1. Go to https://steamcommunity.com/dev/apikey
2. Create a Steam Web API key
3. Add it to your config as `steam_api_key`

Without a Steam API key, author information will show as Steam profile links instead of usernames.

## Usage

### Run once to check for updates:
```bash
python main.py --config config.json
```

### Run continuously with polling:
```bash
python main.py --config config.json --watch 300  # Check every 5 minutes
```

### Update author names for existing mods:
```bash
python main.py --config config.json --update-authors
```

### Using environment variables:
```bash
export DISCORD_WEBHOOK_URL="your_webhook_url"
export STEAM_API_KEY="your_steam_api_key"
python main.py
```

## Database

The tool uses SQLite to store:
- Mod information (title, author, description, stats, etc.)
- Steam user cache (usernames, profile URLs, avatars)
- Last update timestamps

Database file: `mods.db` (configurable with `--db` option)

## Command Line Options

- `--config`: Path to config file (default: config.json)
- `--db`: Path to SQLite database (default: mods.db)  
- `--watch`: Polling interval in seconds (omit for single run)
- `--update-authors`: Update author names for existing mods and exit

## Discord Notification Format

Notifications include:
- Mod title and alias
- Author name (if Steam API key provided)
- Update timestamp
- File size
- View/subscription/favorite counts
- Tags
- Link to Steam Workshop page
