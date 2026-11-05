"""Resource namespaces for the OmniSocials client."""

from .accounts import Accounts, AsyncAccounts
from .ads import AdDrafts, Ads, AsyncAdDrafts, AsyncAds
from .analytics import Analytics, AsyncAnalytics
from .approval_workflows import ApprovalWorkflows, AsyncApprovalWorkflows
from .audio import AsyncAudio, Audio
from .automations import AsyncAutomations, Automations
from .feature_requests import AsyncFeatureRequests, FeatureRequests
from .folders import AsyncFolders, Folders
from .hashtag_sets import AsyncHashtagSets, HashtagSets
from .inbox import AsyncInbox, Inbox
from .limits import AsyncLimits, Limits
from .locations import AsyncLocations, Locations
from .media import AsyncMedia, Media
from .pinterest import AsyncPinterest, Pinterest
from .posts import AsyncPosts, Posts
from .tags import AsyncTags, Tags
from .webhooks import AsyncWebhooks, Webhooks

__all__ = [
    "Posts",
    "AsyncPosts",
    "Media",
    "AsyncMedia",
    "Folders",
    "AsyncFolders",
    "HashtagSets",
    "AsyncHashtagSets",
    "Tags",
    "AsyncTags",
    "Limits",
    "AsyncLimits",
    "FeatureRequests",
    "AsyncFeatureRequests",
    "ApprovalWorkflows",
    "AsyncApprovalWorkflows",
    "Accounts",
    "AsyncAccounts",
    "Analytics",
    "AsyncAnalytics",
    "Locations",
    "AsyncLocations",
    "Audio",
    "AsyncAudio",
    "Pinterest",
    "AsyncPinterest",
    "Automations",
    "AsyncAutomations",
    "Ads",
    "AsyncAds",
    "AdDrafts",
    "AsyncAdDrafts",
    "Inbox",
    "AsyncInbox",
    "Webhooks",
    "AsyncWebhooks",
]
