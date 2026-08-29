"""Locations resource: Instagram and Threads location tagging (search + validate)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Locations", "AsyncLocations"]


class Locations:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def search(
        self,
        q: Optional[str] = None,
        *,
        platform: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Any:
        """``GET /locations/search`` - search locations for post tagging.

        Default (``platform="instagram"``): searches Facebook place pages
        usable as an Instagram ``location_id``.

        With ``platform="threads"``: searches Threads locations by ``q`` or
        around a ``latitude`` + ``longitude`` point (pass either ``q`` or
        the coordinate pair). Use a Threads result's ``id`` as
        ``threads.location_id`` on a post; the two sources use different
        ids (a Facebook Place id is not a Threads location id). The Threads
        response shape also differs: ``{"locations": [...]}`` on success,
        or ``{"error": {"code", "message"}}`` on the degraded path (codes:
        ``not_available``, ``threads_not_connected``,
        ``threads_reauth_required``, ``platform_error``). Threads location
        tagging is currently rolling out; until Meta approves the
        permissions it is disabled on production and calls return a clear
        error.
        """
        return self._client.request(
            "GET",
            "/locations/search",
            query={
                "q": q,
                "platform": platform,
                "latitude": latitude,
                "longitude": longitude,
            },
        )

    def validate(self, id: str) -> Any:
        """``GET /locations/validate?id=`` - validate a location id before
        attaching it to a post."""
        return self._client.request("GET", "/locations/validate", query={"id": id})


class AsyncLocations:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def search(
        self,
        q: Optional[str] = None,
        *,
        platform: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Any:
        """``GET /locations/search`` - search locations for post tagging.

        Default (``platform="instagram"``): searches Facebook place pages
        usable as an Instagram ``location_id``.

        With ``platform="threads"``: searches Threads locations by ``q`` or
        around a ``latitude`` + ``longitude`` point (pass either ``q`` or
        the coordinate pair). Use a Threads result's ``id`` as
        ``threads.location_id`` on a post; the two sources use different
        ids (a Facebook Place id is not a Threads location id). The Threads
        response shape also differs: ``{"locations": [...]}`` on success,
        or ``{"error": {"code", "message"}}`` on the degraded path (codes:
        ``not_available``, ``threads_not_connected``,
        ``threads_reauth_required``, ``platform_error``). Threads location
        tagging is currently rolling out; until Meta approves the
        permissions it is disabled on production and calls return a clear
        error.
        """
        return await self._client.request(
            "GET",
            "/locations/search",
            query={
                "q": q,
                "platform": platform,
                "latitude": latitude,
                "longitude": longitude,
            },
        )

    async def validate(self, id: str) -> Any:
        """``GET /locations/validate?id=`` - validate a location id before
        attaching it to a post."""
        return await self._client.request(
            "GET", "/locations/validate", query={"id": id}
        )
