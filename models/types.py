"""Type definitions for workshop-watcher."""
from typing import TypedDict, Optional, List, Dict, Any

class ModData(TypedDict, total=False):
    """Database mod record."""
    id: int
    title: Optional[str]
    author_id: Optional[str]
    author_name: Optional[str]
    file_size: Optional[int]
    time_created: Optional[int]
    time_updated: Optional[int]
    last_checked: int
    description: Optional[str]
    views: Optional[int]
    subscriptions: Optional[int]
    favorites: Optional[int]
    tags: Optional[str]
    visibility: Optional[int]
    preview_url: Optional[str]

class WorkshopItem(TypedDict):
    """Workshop item from config."""
    id: int
    name: Optional[str]

class DiscordEmbed(TypedDict, total=False):
    """Discord embed structure."""
    title: str
    url: str
    description: str
    color: int
    fields: List[Dict[str, Any]]
    footer: Dict[str, str]
    timestamp: str
