"""Locations resource: Instagram place tagging (search + validate)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Locations", "AsyncLocations"]


class Locations:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def search(self, q: str) -> Any:
        """``GET /locations/search?q=`` - search Facebook place pages usable
        as an Instagram ``location_id``."""
        return self._client.request("GET", "/locations/search", query={"q": q})

    def validate(self, id: str) -> Any:
        """``GET /locations/validate?id=`` - validate a location id before
        attaching it to a post."""
        return self._client.request("GET", "/locations/validate", query={"id": id})


class AsyncLocations:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def search(self, q: str) -> Any:
        """``GET /locations/search?q=`` - search Facebook place pages usable
        as an Instagram ``location_id``."""
        return await self._client.request("GET", "/locations/search", query={"q": q})

    async def validate(self, id: str) -> Any:
        """``GET /locations/validate?id=`` - validate a location id before
        attaching it to a post."""
        return await self._client.request(
            "GET", "/locations/validate", query={"id": id}
        )
