"""Official Python SDK for the OmniSocials Public API.

Docs: https://docs.omnisocials.com
"""

from ._client import AsyncOmniSocials, OmniSocials
from ._errors import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    NotFoundError,
    OmniSocialsError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    ValidationError,
    WebhookVerificationError,
)
from ._utils import NOT_GIVEN, NotGiven
from ._webhooks import verify_webhook_signature

__version__ = "0.1.0"

__all__ = [
    "OmniSocials",
    "AsyncOmniSocials",
    "verify_webhook_signature",
    "OmniSocialsError",
    "APIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "APIConnectionError",
    "WebhookVerificationError",
    "NOT_GIVEN",
    "NotGiven",
    "__version__",
]
