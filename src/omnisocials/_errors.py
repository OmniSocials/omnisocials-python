"""Error hierarchy for the OmniSocials SDK.

OmniSocialsError (base)
  APIError (has .status, .code, .message, .body)
    AuthenticationError (401)
    PermissionDeniedError (403)
    NotFoundError (404)
    ValidationError (400 / 422)
    RateLimitError (429, exposes .retry_after seconds when known)
    ServerError (>= 500)
  APIConnectionError (network failure / timeout)
  WebhookVerificationError
"""

from __future__ import annotations

from typing import Any, Optional

__all__ = [
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
]


class OmniSocialsError(Exception):
    """Base class for every error raised by this SDK."""


class APIError(OmniSocialsError):
    """A non-2xx response from the OmniSocials API.

    Attributes:
        status: HTTP status code (``None`` for client-side failures such as a
            missing API key at construction time).
        code: Machine-readable error code from the API body
            (``{"error": {"code": ..., "message": ...}}``) when present.
        message: Human-readable error message.
        body: The parsed response body (dict) when the response was JSON,
            otherwise the raw response text, or ``None``.
    """

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        code: Optional[str] = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.body = body

    def __str__(self) -> str:
        parts = []
        if self.status is not None:
            parts.append(f"status={self.status}")
        if self.code:
            parts.append(f"code={self.code}")
        prefix = f"[{', '.join(parts)}] " if parts else ""
        return f"{prefix}{self.message}"


class AuthenticationError(APIError):
    """401 - missing or invalid API key."""


class PermissionDeniedError(APIError):
    """403 - the API key lacks the required scope."""


class NotFoundError(APIError):
    """404 - the requested resource does not exist."""


class ValidationError(APIError):
    """400 / 422 - the request was malformed or failed validation."""


class RateLimitError(APIError):
    """429 - rate limit exceeded (100 requests per minute).

    ``retry_after`` is the number of seconds to wait before retrying, taken
    from the ``Retry-After`` header (or the body's ``retry_after`` field)
    when present.
    """

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = 429,
        code: Optional[str] = None,
        body: Any = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(message, status=status, code=code, body=body)
        self.retry_after = retry_after


class ServerError(APIError):
    """>= 500 - something went wrong on OmniSocials' side."""


class APIConnectionError(OmniSocialsError):
    """The request never got a response (network failure or timeout)."""

    def __init__(self, message: str = "Connection error.") -> None:
        super().__init__(message)
        self.message = message


class WebhookVerificationError(OmniSocialsError):
    """Webhook signature verification failed."""
