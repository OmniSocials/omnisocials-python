"""Hashtag sets resource: saved, reusable hashtag groups applied to posts at
create time (via ``hashtag_set`` / ``hashtag_set_id`` on posts.create)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from .._utils import drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["HashtagSets", "AsyncHashtagSets"]

# ``hashtags`` is a list of tags, or a single string of tags.
HashtagsType = Union[str, Sequence[str]]


class HashtagSets:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /hashtag-sets`` - list the workspace's saved hashtag sets."""
        return self._client.request("GET", "/hashtag-sets")

    def get(self, hashtag_set_id: str) -> Any:
        """``GET /hashtag-sets/{id}`` - fetch a single hashtag set."""
        return self._client.request("GET", f"/hashtag-sets/{hashtag_set_id}")

    def create(self, *, name: str, hashtags: HashtagsType) -> Any:
        """``POST /hashtag-sets`` - create a hashtag set.

        ``hashtags`` is a list of tags, or a single string of tags. Apply the
        set on posts.create via ``hashtag_set`` (name, case-insensitive) or
        ``hashtag_set_id``.
        """
        return self._client.request(
            "POST", "/hashtag-sets", json={"name": name, "hashtags": hashtags}
        )

    def update(
        self,
        hashtag_set_id: str,
        *,
        name: Optional[str] = None,
        hashtags: Optional[HashtagsType] = None,
    ) -> Any:
        """``PATCH /hashtag-sets/{id}`` - rename and/or replace the tags.

        ``hashtags`` replaces the FULL list.
        """
        body = drop_none({"name": name, "hashtags": hashtags})
        return self._client.request(
            "PATCH", f"/hashtag-sets/{hashtag_set_id}", json=body
        )

    def delete(self, hashtag_set_id: str) -> None:
        """``DELETE /hashtag-sets/{id}`` - delete a hashtag set. Returns
        ``None`` (204)."""
        return self._client.request("DELETE", f"/hashtag-sets/{hashtag_set_id}")


class AsyncHashtagSets:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /hashtag-sets`` - list the workspace's saved hashtag sets."""
        return await self._client.request("GET", "/hashtag-sets")

    async def get(self, hashtag_set_id: str) -> Any:
        """``GET /hashtag-sets/{id}`` - fetch a single hashtag set."""
        return await self._client.request("GET", f"/hashtag-sets/{hashtag_set_id}")

    async def create(self, *, name: str, hashtags: HashtagsType) -> Any:
        """``POST /hashtag-sets`` - create a hashtag set.

        ``hashtags`` is a list of tags, or a single string of tags.
        """
        return await self._client.request(
            "POST", "/hashtag-sets", json={"name": name, "hashtags": hashtags}
        )

    async def update(
        self,
        hashtag_set_id: str,
        *,
        name: Optional[str] = None,
        hashtags: Optional[HashtagsType] = None,
    ) -> Any:
        """``PATCH /hashtag-sets/{id}`` - rename and/or replace the tags.

        ``hashtags`` replaces the FULL list.
        """
        body = drop_none({"name": name, "hashtags": hashtags})
        return await self._client.request(
            "PATCH", f"/hashtag-sets/{hashtag_set_id}", json=body
        )

    async def delete(self, hashtag_set_id: str) -> None:
        """``DELETE /hashtag-sets/{id}`` - delete a hashtag set. Returns
        ``None`` (204)."""
        return await self._client.request(
            "DELETE", f"/hashtag-sets/{hashtag_set_id}"
        )
