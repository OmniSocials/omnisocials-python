"""Analytics resource: post stats, account stats, overview, and best times."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from .._utils import join_list

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Analytics", "AsyncAnalytics"]


class Analytics:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def post(self, post_id: str) -> Any:
        """``GET /analytics/posts/{id}`` - latest per-platform metrics for one post."""
        return self._client.request("GET", f"/analytics/posts/{post_id}")

    def posts(self, ids: Union[str, Sequence[str]]) -> Any:
        """``GET /analytics/posts?ids=a,b,c`` - bulk metrics for up to 100
        posts in one request. ``ids`` is a list of post ids (or an
        already-joined comma-separated string)."""
        return self._client.request(
            "GET", "/analytics/posts", query={"ids": join_list(ids)}
        )

    def overview(
        self,
        *,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Any:
        """``GET /analytics/overview`` - workspace-wide analytics overview."""
        return self._client.request(
            "GET",
            "/analytics/overview",
            query={"period": period, "start_date": start_date, "end_date": end_date},
        )

    def accounts(
        self,
        *,
        platform: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Any:
        """``GET /analytics/accounts`` - account-level stats (followers etc.)."""
        return self._client.request(
            "GET", "/analytics/accounts", query={"platform": platform, "date": date}
        )

    def best_times(self, *, platform: str, timezone: Optional[str] = None) -> Any:
        """``GET /analytics/best-times`` - best times to post for a platform,
        derived from the workspace's own engagement history."""
        return self._client.request(
            "GET",
            "/analytics/best-times",
            query={"platform": platform, "timezone": timezone},
        )


class AsyncAnalytics:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def post(self, post_id: str) -> Any:
        """``GET /analytics/posts/{id}`` - latest per-platform metrics for one post."""
        return await self._client.request("GET", f"/analytics/posts/{post_id}")

    async def posts(self, ids: Union[str, Sequence[str]]) -> Any:
        """``GET /analytics/posts?ids=a,b,c`` - bulk metrics for up to 100 posts."""
        return await self._client.request(
            "GET", "/analytics/posts", query={"ids": join_list(ids)}
        )

    async def overview(
        self,
        *,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Any:
        """``GET /analytics/overview`` - workspace-wide analytics overview."""
        return await self._client.request(
            "GET",
            "/analytics/overview",
            query={"period": period, "start_date": start_date, "end_date": end_date},
        )

    async def accounts(
        self,
        *,
        platform: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Any:
        """``GET /analytics/accounts`` - account-level stats (followers etc.)."""
        return await self._client.request(
            "GET", "/analytics/accounts", query={"platform": platform, "date": date}
        )

    async def best_times(
        self, *, platform: str, timezone: Optional[str] = None
    ) -> Any:
        """``GET /analytics/best-times`` - best times to post for a platform."""
        return await self._client.request(
            "GET",
            "/analytics/best-times",
            query={"platform": platform, "timezone": timezone},
        )
