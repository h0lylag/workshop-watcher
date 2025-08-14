#!/usr/bin/env python3

import json
from steam import fetch_published_file_details

# Test the Steam API response for your mod
mod_id = 3458840545
details = fetch_published_file_details([mod_id])

if mod_id in details:
    print("Raw Steam API response:")
    print(json.dumps(details[mod_id], indent=2))
else:
    print("No data found for mod ID:", mod_id)
