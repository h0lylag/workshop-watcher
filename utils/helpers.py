import time
from typing import Dict, Iterable, List, Iterator

def get_current_timestamp() -> int:
    """Get current Unix timestamp."""
    return int(time.time())

def chunk_list(items: List, chunk_size: int) -> Iterator[List]:
    """Split list into chunks of specified size."""
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]

def create_empty_mod_record(mod_id: int) -> Dict:
    """Create empty mod record when Steam API returns no data."""
    return {
        "id": mod_id,
        "last_checked": get_current_timestamp(),
        **{field: None for field in [
            "title", "author_id", "author_name", "file_size",
            "time_created", "time_updated", "description",
            "views", "subscriptions", "favorites", "tags",
            "visibility", "preview_url"
        ]}
    }
