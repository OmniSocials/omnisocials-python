"""Credits resource: the organisation's credit balance and what X statistics
cost. Top-ups are made in the OmniSocials app (Settings -> Organisation ->
Billing -> Credits)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Credits", "AsyncCredits"]


class Credits:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def get(self) -> Any:
        """``GET /credits`` - the balance and the X statistics overview.

        Returns ``{"data": {"balance", "auto_refill": {"enabled"},
        "this_month": {reason: credits}, "x_statistics": {"state",
        "paused_at", "charging": {"active", "from"}, "prices": {"post_read",
        "media_read", "follower_read"}, "total_credits_month", "this_month":
        {"post_reads", "media_reads", "follower_reads", "refreshes",
        "credits"}, "accounts": [{"account_id", "workspace_id", "handle",
        "posts", "followers", "tweets_30d", "credits_month"}]}}}``. 1 credit
        = EUR 0.01. Needs the opt-in scope ``credits:read`` and billing
        rights (manage_billing) for the key's creator; OmniSocials Connect
        keys get ``403 not_available_for_connect``.
        """
        return self._client.request("GET", "/credits")


class AsyncCredits:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def get(self) -> Any:
        """``GET /credits`` - the balance and the X statistics overview (see
        :meth:`Credits.get`)."""
        return await self._client.request("GET", "/credits")
