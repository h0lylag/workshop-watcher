# Workshop Watcher

A robust Steam Workshop monitoring tool that tracks mod updates and sends Discord notifications with comprehensive logging and error handling.

## Features

- **Steam Workshop Monitoring**: Track multiple Steam Workshop mods for updates
- **Discord Notifications**: Rich embed notifications for new and updated mods
- **Steam User Resolution**: Automatically resolves Steam IDs to usernames with intelligent caching
- **Robust Error Handling**: Handles rate limiting, network errors, and API failures gracefully
- **Comprehensive Logging**: Configurable logging with rotation and multiple output options
- **Database Caching**: SQLite database for persistent mod and user data storage
- **Changelog Links**: Direct links to Steam Workshop changelog pages

## Installation

1. Clone or download the project files
2. Install Python 3.8+ (tested with Python 3.12)
3. Get a Steam API key from [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
4. Set up a Discord webhook in your server

## Configuration

### First Run
Run the script once to generate a default config file:
```bash
python3 main.py
```

### Config File (`config.json`)
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

### Environment Variables (Optional)
- `DISCORD_WEBHOOK_URL`: Override webhook URL from config
- `STEAM_API_KEY`: Override Steam API key from config

## Usage

### Basic Usage
```bash
# Check once and exit
python3 main.py

# Monitor continuously (check every 300 seconds)
python3 main.py --watch 300

# Update author names for existing mods
python3 main.py --update-authors
```

### Logging Options
```bash
# Custom log file and level
python3 main.py --log-file /path/to/logfile.log --log-level DEBUG

# Log to file only (no console output)
python3 main.py --no-console

# Available log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
python3 main.py --log-level WARNING
```

### All Options
```bash
python3 main.py --help
```

## Discord Notifications

The tool sends rich Discord embeds containing:

### For New Mods
- Message: "Workshop mod added" or "Workshop mods added"
- Mod title with Steam Workshop link
- Creator name with Steam profile link
- Created and updated timestamps (Discord format)
- File size and changelog link
- Statistics (views, subscriptions, favorites)
- Mod preview image (if available)

### For Updated Mods
- Message: "Workshop mod updated" or "Workshop mods updated"
- Same information as new mods
- Additional "Previous update" field showing last update time

## Database

The tool uses SQLite to store:
- **Mod Data**: Titles, descriptions, timestamps, statistics
- **Steam Users**: Cached usernames to reduce API calls (7-day cache)

Database file: `mods.db` (configurable with `--db` option)

## Error Handling

### Discord Rate Limiting
- Automatically detects 429 responses
- Respects `Retry-After` headers
- Implements exponential backoff
- Retries up to 5 times per request

### Network Issues
- Automatic retry with exponential backoff
- Graceful handling of timeouts and connection errors
- Continues operation even if some requests fail

### Steam API Issues
- Handles invalid mod IDs gracefully
- Continues processing other mods if some fail
- Caches failed user lookups to avoid repeated failures

## Logging

### Features
- **Rotating Logs**: Automatically rotates when files reach 10MB
- **Configurable Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Dual Output**: Console and file logging (configurable)
- **Structured Format**: Timestamps, modules, line numbers
- **Exception Tracking**: Full tracebacks for debugging

### Log Files
- Default: `workshop-watcher.log`
- Rotated files: `workshop-watcher.log.1`, `workshop-watcher.log.2`, etc.
- Keeps 5 backup files by default

## Troubleshooting

### Common Issues

1. **No Discord notifications**
   - Check webhook URL is correct
   - Verify Discord server permissions
   - Check logs for rate limiting or network errors

2. **Steam API errors**
   - Verify Steam API key is valid
   - Check if Steam is down: [https://steamstat.us/](https://steamstat.us/)
   - Review rate limiting in logs

3. **Database errors**
   - Ensure write permissions in directory
   - Check disk space
   - Delete database file to reset if corrupted

### Debug Mode
Enable debug logging to see detailed operation:
```bash
python3 main.py --log-level DEBUG
```

## File Structure

```
workshop-watcher/
├── main.py              # Entry point and argument parsing
├── config.py            # Configuration loading and validation
├── watcher.py           # Main polling and coordination logic
├── steam.py             # Steam API integration
├── discord.py           # Discord webhook and embed handling
├── db.py                # Database operations
├── user_resolver.py     # Steam user caching and resolution
├── util.py              # Utility functions
├── logger.py            # Centralized logging setup
├── config.json          # Configuration file (created on first run)
├── mods.db              # SQLite database (created automatically)
└── workshop-watcher.log # Log file (created automatically)
```

## Performance

- **Batch Processing**: Processes up to 50 mods per Steam API call
- **User Caching**: 7-day cache for Steam usernames
- **Rate Limiting**: Respects all API rate limits
- **Memory Efficient**: Processes mods in chunks to avoid memory issues

## Security

- **API Key Protection**: Never logs API keys
- **Webhook Protection**: Truncates webhook URLs in logs
- **Input Validation**: Validates all configuration inputs
- **Error Sanitization**: Sanitizes error messages in logs

## License

This project is open source. Use responsibly and respect Steam's Terms of Service.
