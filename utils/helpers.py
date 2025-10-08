import time
from typing import Dict, Iterable

def now_ts() -> int:
    return int(time.time())

def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

def create_empty_mod_record(mod_id: int) -> Dict:
    """Create empty mod record when Steam API returns no data."""
    return {
        "id": mod_id,
        "last_checked": now_ts(),
        **{field: None for field in [
            "title", "author_id", "author_name", "file_size",
            "time_created", "time_updated", "description",
            "views", "subscriptions", "favorites", "tags",
            "visibility", "preview_url"
        ]}
    }
