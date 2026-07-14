"""Webhooks resource: manage event subscriptions (post.scheduled,
post.published, post.failed)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence

from .._utils import drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Webhooks", "AsyncWebhooks"]


class Webhooks:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /webhooks`` - list webhook subscriptions."""
        return self._client.request("GET", "/webhooks")

    def get(self, webhook_id: str) -> Any:
        """``GET /webhooks/{id}`` - fetch a single webhook subscription."""
        return self._client.request("GET", f"/webhooks/{webhook_id}")

    def create(self, *, url: str, events: Sequence[str]) -> Any:
        """``POST /webhooks`` - create a webhook subscription.

        ``url`` must be HTTPS. ``events`` is a non-empty subset of
        ``post.scheduled``, ``post.published``, ``post.failed``. The signing
        ``secret`` is only returned once, in this response - store it.
        """
        return self._client.request(
            "POST", "/webhooks", json={"url": url, "events": list(events)}
        )

    def update(
        self,
        webhook_id: str,
        *,
        url: Optional[str] = None,
        events: Optional[Sequence[str]] = None,
        is_active: Optional[bool] = None,
    ) -> Any:
        """``PATCH /webhooks/{id}`` - update url, events, or active state."""
        body = drop_none(
            {
                "url": url,
                "events": list(events) if events is not None else None,
                "is_active": is_active,
            }
        )
        return self._client.request("PATCH", f"/webhooks/{webhook_id}", json=body)

    def delete(self, webhook_id: str) -> None:
        """``DELETE /webhooks/{id}`` - delete a webhook. Returns ``None`` (204)."""
        return self._client.request("DELETE", f"/webhooks/{webhook_id}")

    def rotate_secret(self, webhook_id: str) -> Any:
        """``POST /webhooks/{id}/rotate-secret`` - rotate the signing secret.

        The new secret is only returned once, in this response.
        """
        return self._client.request("POST", f"/webhooks/{webhook_id}/rotate-secret")


class AsyncWebhooks:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /webhooks`` - list webhook subscriptions."""
        return await self._client.request("GET", "/webhooks")

    async def get(self, webhook_id: str) -> Any:
        """``GET /webhooks/{id}`` - fetch a single webhook subscription."""
        return await self._client.request("GET", f"/webhooks/{webhook_id}")

    async def create(self, *, url: str, events: Sequence[str]) -> Any:
        """``POST /webhooks`` - create a webhook subscription.

        The signing ``secret`` is only returned once, in this response.
        """
        return await self._client.request(
            "POST", "/webhooks", json={"url": url, "events": list(events)}
        )

    async def update(
        self,
        webhook_id: str,
        *,
        url: Optional[str] = None,
        events: Optional[Sequence[str]] = None,
        is_active: Optional[bool] = None,
    ) -> Any:
        """``PATCH /webhooks/{id}`` - update url, events, or active state."""
        body = drop_none(
            {
                "url": url,
                "events": list(events) if events is not None else None,
                "is_active": is_active,
            }
        )
        return await self._client.request(
            "PATCH", f"/webhooks/{webhook_id}", json=body
        )

    async def delete(self, webhook_id: str) -> None:
        """``DELETE /webhooks/{id}`` - delete a webhook. Returns ``None`` (204)."""
        return await self._client.request("DELETE", f"/webhooks/{webhook_id}")

    async def rotate_secret(self, webhook_id: str) -> Any:
        """``POST /webhooks/{id}/rotate-secret`` - rotate the signing secret."""
        return await self._client.request(
            "POST", f"/webhooks/{webhook_id}/rotate-secret"
        )
