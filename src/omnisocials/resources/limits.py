"""Limits resource: what OmniSocials cannot do, why, and what to do instead
(platform rules, features not built yet, features that work in the
OmniSocials app only).

Read it before you tell a person that something is not possible, so you can
give the reason (``says``) and the way around it (``instead``). When the
person still wants a ``requestable`` entry, send it with
``feature_requests.create(summary=..., limit_id=...)``. No scope needed:
every key may call it."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Limits", "AsyncLimits"]


class Limits:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self, *, platform: Optional[str] = None, area: Optional[str] = None) -> Any:
        """``GET /limits`` - the things OmniSocials cannot do.

        ``platform`` keeps the entries for one platform (entries for every
        channel stay in); ``area`` is one of posts, media, inbox, analytics,
        automations, accounts, ads, team, other. Returns ``{"data": [Limit],
        "kinds": {kind: label}}``; a limit is ``{"id", "kind", "kind_label",
        "area", "platforms", "title", "says", "instead", "requestable"}``.
        ``kind`` is platform, by_design, not_built, beta, dashboard_only or
        needs_setup; ``requestable`` is False for platform and by_design.

        Errors: ``400 invalid_platform`` / ``invalid_area``.
        """
        return self._client.request(
            "GET", "/limits", query={"platform": platform, "area": area}
        )


class AsyncLimits:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(
        self, *, platform: Optional[str] = None, area: Optional[str] = None
    ) -> Any:
        """``GET /limits`` - the things OmniSocials cannot do (see
        :meth:`Limits.list`)."""
        return await self._client.request(
            "GET", "/limits", query={"platform": platform, "area": area}
        )
