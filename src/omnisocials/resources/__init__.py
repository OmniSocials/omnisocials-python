"""Resource namespaces for the OmniSocials client."""

from .accounts import Accounts, AsyncAccounts
from .analytics import Analytics, AsyncAnalytics
from .audio import AsyncAudio, Audio
from .folders import AsyncFolders, Folders
from .locations import AsyncLocations, Locations
from .media import AsyncMedia, Media
from .posts import AsyncPosts, Posts
from .webhooks import AsyncWebhooks, Webhooks

__all__ = [
    "Posts",
    "AsyncPosts",
    "Media",
    "AsyncMedia",
    "Folders",
    "AsyncFolders",
    "Accounts",
    "AsyncAccounts",
    "Analytics",
    "AsyncAnalytics",
    "Locations",
    "AsyncLocations",
    "Audio",
    "AsyncAudio",
    "Webhooks",
    "AsyncWebhooks",
]
