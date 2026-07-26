"""Core HTTP transport for the OmniSocials SDK (sync + async)."""

from __future__ import annotations

import asyncio
import email.utils
import os
import random
import time
from typing import Any, Dict, Mapping, Optional, Tuple

import httpx

from ._errors import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from ._utils import NOT_GIVEN, NotGiven
from .resources.accounts import Accounts, AsyncAccounts
from .resources.analytics import Analytics, AsyncAnalytics
from .resources.audio import AsyncAudio, Audio
from .resources.folders import AsyncFolders, Folders
from .resources.hashtag_sets import AsyncHashtagSets, HashtagSets
from .resources.inbox import AsyncInbox, Inbox
from .resources.locations import AsyncLocations, Locations
from .resources.media import AsyncMedia, Media
from .resources.posts import AsyncPosts, Posts
from .resources.webhooks import AsyncWebhooks, Webhooks

__all__ = ["OmniSocials", "AsyncOmniSocials", "NOT_GIVEN", "NotGiven"]

VERSION = "0.2.0"
DEFAULT_BASE_URL = "https://api.omnisocials.com/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
USER_AGENT = f"omnisocials-python/{VERSION}"

# Statuses that are retried automatically (alongside connection errors).
_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_MAX_BACKOFF_SECONDS = 8.0


def _serialize_query(params: Optional[Mapping[str, Any]]) -> Optional[Dict[str, str]]:
    """Stringify query params, dropping None/NOT_GIVEN values."""
    if not params:
        return None
    out: Dict[str, str] = {}
    for key, value in params.items():
        if value is None or isinstance(value, NotGiven):
            continue
        if isinstance(value, bool):
            out[key] = "true" if value else "false"
        else:
            out[key] = str(value)
    return out or None


def _parse_retry_after(response: httpx.Response, body: Any) -> Optional[float]:
    header = response.headers.get("retry-after")
    if header is not None:
        try:
            return max(0.0, float(header))
        except ValueError:
            try:
                dt = email.utils.parsedate_to_datetime(header)
                return max(0.0, dt.timestamp() - time.time())
            except (TypeError, ValueError):
                pass
    if isinstance(body, dict):
        value = body.get("retry_after")
        if isinstance(value, (int, float)):
            return max(0.0, float(value))
    return None


def _parse_body(response: httpx.Response) -> Any:
    """Parse a response body as JSON, falling back to raw text."""
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


def _error_from_response(response: httpx.Response) -> APIError:
    body = _parse_body(response)
    status = response.status_code

    code: Optional[str] = None
    message = f"Request failed with status {status}."
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            if isinstance(error.get("code"), str):
                code = error["code"]
            if isinstance(error.get("message"), str):
                message = error["message"]
        elif isinstance(body.get("message"), str):
            message = body["message"]

    if status == 401:
        return AuthenticationError(message, status=status, code=code, body=body)
    if status == 403:
        return PermissionDeniedError(message, status=status, code=code, body=body)
    if status == 404:
        return NotFoundError(message, status=status, code=code, body=body)
    if status in (400, 422):
        return ValidationError(message, status=status, code=code, body=body)
    if status == 429:
        return RateLimitError(
            message,
            status=status,
            code=code,
            body=body,
            retry_after=_parse_retry_after(response, body),
        )
    if status >= 500:
        return ServerError(message, status=status, code=code, body=body)
    return APIError(message, status=status, code=code, body=body)


def _backoff_delay(attempt: int, retry_after: Optional[float]) -> float:
    """Delay before retry number ``attempt`` (0-based): 0.5s, 1s, 2s... + jitter.

    An explicit ``Retry-After`` from the server wins over the computed backoff.
    """
    if retry_after is not None:
        return min(retry_after, 60.0)
    delay = min(0.5 * (2**attempt), _MAX_BACKOFF_SECONDS)
    return delay * (0.75 + random.random() * 0.5)


class _BaseClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        key = api_key or os.environ.get("OMNISOCIALS_API_KEY")
        if not key:
            raise AuthenticationError(
                "No API key provided. Pass api_key=... to the client or set the "
                "OMNISOCIALS_API_KEY environment variable. Create a key in the "
                "OmniSocials app under Settings -> API Keys.",
                status=None,
            )
        self.api_key = key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))

    def _default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @staticmethod
    def _handle_response(response: httpx.Response) -> Any:
        if response.status_code == 204:
            return None
        if 200 <= response.status_code < 300:
            return _parse_body(response)
        raise _error_from_response(response)

    @staticmethod
    def _should_retry(response: httpx.Response) -> Tuple[bool, Optional[float]]:
        if response.status_code in _RETRY_STATUSES or response.status_code >= 500:
            return True, _parse_retry_after(response, _parse_body(response))
        return False, None


class OmniSocials(_BaseClient):
    """Synchronous OmniSocials API client.

    Usage::

        from omnisocials import OmniSocials

        client = OmniSocials()  # reads OMNISOCIALS_API_KEY from env
        # or: OmniSocials(api_key="omsk_live_...", base_url=..., timeout=..., max_retries=...)

        post = client.posts.create(
            content="Hello from the SDK",
            channels=["instagram", "linkedin"],
            scheduled_at="2026-08-01T09:00:00Z",
        )

    Supports use as a context manager; call ``close()`` when done otherwise.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        super().__init__(
            api_key, base_url=base_url, timeout=timeout, max_retries=max_retries
        )
        self._http = httpx.Client(timeout=timeout, headers=self._default_headers())

        self.posts = Posts(self)
        self.media = Media(self)
        self.folders = Folders(self)
        self.hashtag_sets = HashtagSets(self)
        self.accounts = Accounts(self)
        self.analytics = Analytics(self)
        self.locations = Locations(self)
        self.audio = Audio(self)
        self.inbox = Inbox(self)
        self.webhooks = Webhooks(self)

    # -- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "OmniSocials":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    # -- transport ---------------------------------------------------------
    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        json: Optional[Mapping[str, Any]] = None,
        files: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        url = self._build_url(path)
        params = _serialize_query(query)

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._http.request(
                    method, url, params=params, json=json, files=files, data=data
                )
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(_backoff_delay(attempt, None))
                continue

            should_retry, retry_after = self._should_retry(response)
            if should_retry and attempt < self.max_retries:
                time.sleep(_backoff_delay(attempt, retry_after))
                continue
            return self._handle_response(response)

        raise APIConnectionError(
            f"Connection error while requesting {method} {url}: {last_exc}"
        ) from last_exc

    # -- misc --------------------------------------------------------------
    def health(self) -> Any:
        """``GET /health`` - API health check (no scopes required)."""
        return self.request("GET", "/health")


class AsyncOmniSocials(_BaseClient):
    """Asynchronous OmniSocials API client (httpx.AsyncClient).

    Usage::

        from omnisocials import AsyncOmniSocials

        async with AsyncOmniSocials() as client:
            post = await client.posts.create(
                content="Hello from the SDK",
                channels=["instagram"],
            )

    Supports ``async with``; call ``await client.aclose()`` when done otherwise.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        super().__init__(
            api_key, base_url=base_url, timeout=timeout, max_retries=max_retries
        )
        self._http = httpx.AsyncClient(timeout=timeout, headers=self._default_headers())

        self.posts = AsyncPosts(self)
        self.media = AsyncMedia(self)
        self.folders = AsyncFolders(self)
        self.hashtag_sets = AsyncHashtagSets(self)
        self.accounts = AsyncAccounts(self)
        self.analytics = AsyncAnalytics(self)
        self.locations = AsyncLocations(self)
        self.audio = AsyncAudio(self)
        self.inbox = AsyncInbox(self)
        self.webhooks = AsyncWebhooks(self)

    # -- lifecycle ---------------------------------------------------------
    async def aclose(self) -> None:
        await self._http.aclose()

    # Alias so both clients expose a close(); prefer aclose() in async code.
    close = aclose

    async def __aenter__(self) -> "AsyncOmniSocials":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()

    # -- transport ---------------------------------------------------------
    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        json: Optional[Mapping[str, Any]] = None,
        files: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        url = self._build_url(path)
        params = _serialize_query(query)

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._http.request(
                    method, url, params=params, json=json, files=files, data=data
                )
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(_backoff_delay(attempt, None))
                continue

            should_retry, retry_after = self._should_retry(response)
            if should_retry and attempt < self.max_retries:
                await asyncio.sleep(_backoff_delay(attempt, retry_after))
                continue
            return self._handle_response(response)

        raise APIConnectionError(
            f"Connection error while requesting {method} {url}: {last_exc}"
        ) from last_exc

    # -- misc --------------------------------------------------------------
    async def health(self) -> Any:
        """``GET /health`` - API health check (no scopes required)."""
        return await self.request("GET", "/health")
