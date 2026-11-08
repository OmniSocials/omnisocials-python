"""Analytics resource: post stats, account stats, overview, and best times."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from .._utils import join_list, path_segment
from .tags import TagFilter, tag_query

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Analytics", "AsyncAnalytics"]


class Analytics:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def post(self, post_id: str) -> Any:
        """``GET /analytics/posts/{id}`` - latest per-platform metrics for one post."""
        return self._client.request("GET", f"/analytics/posts/{path_segment(post_id)}")

    def posts(self, ids: Union[str, Sequence[str]]) -> Any:
        """``GET /analytics/posts?ids=a,b,c`` - bulk metrics for up to 100
        posts in one request. ``ids`` is a list of post ids (or an
        already-joined comma-separated string). Each entry also carries
        ``tags`` (the post's tags) and ``trial_reel`` (``{"strategy":
        "MANUAL" | "SS_PERFORMANCE"}`` for an Instagram Trial Reel, else
        ``None``)."""
        return self._client.request(
            "GET", "/analytics/posts", query={"ids": join_list(ids)}
        )

    def overview(
        self,
        *,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tag: Optional[TagFilter] = None,
    ) -> Any:
        """``GET /analytics/overview`` - workspace-wide analytics overview.

        ``tag`` (a tag id or name, or a list: any of them) keeps the post
        numbers of the posts with that tag; account numbers stay those of
        the whole account. An unknown tag is a ``404 tag_not_found``."""
        return self._client.request(
            "GET",
            "/analytics/overview",
            query={
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "tag": tag_query(tag),
            },
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
        derived from the workspace's own engagement history. The response has
        no ``data`` wrapper: ``platform``, ``timezone``, ``basis``, ``grid`` and
        ``recommendations`` sit at the top level."""
        return self._client.request(
            "GET",
            "/analytics/best-times",
            query={"platform": platform, "timezone": timezone},
        )

    def tags(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        platform: Optional[str] = None,
        min_posts: Optional[int] = None,
    ) -> Any:
        """``GET /analytics/tags`` - how each tag did against your normal,
        for the published posts in a period (default the last 90 days).

        Returns ``{"data": {"period", "platform", "min_posts", "tags",
        "untagged", "normals"}}``. Each entry of ``tags`` is ``{"tag",
        "posts", "measured", "median_impressions", "engagement_rate"
        (percent), "vs_normal" (fraction: 0.38 = 38% above your normal),
        "best_channel", "enough_posts"}``, comparable tags first, best
        first; ``untagged`` has the same numbers for the posts without a
        tag, ``normals`` the median impressions per channel. ``platform``
        keeps one channel's numbers; ``min_posts`` (1 to 50, default 5) is
        the measured posts a tag needs before ``enough_posts`` is true.
        """
        return self._client.request(
            "GET",
            "/analytics/tags",
            query={
                "start_date": start_date,
                "end_date": end_date,
                "platform": platform,
                "min_posts": min_posts,
            },
        )


class AsyncAnalytics:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def post(self, post_id: str) -> Any:
        """``GET /analytics/posts/{id}`` - latest per-platform metrics for one post."""
        return await self._client.request("GET", f"/analytics/posts/{path_segment(post_id)}")

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
        tag: Optional[TagFilter] = None,
    ) -> Any:
        """``GET /analytics/overview`` - workspace-wide analytics overview.

        ``tag`` (a tag id or name, or a list: any of them) keeps the post
        numbers of the posts with that tag; account numbers stay those of
        the whole account. An unknown tag is a ``404 tag_not_found``."""
        return await self._client.request(
            "GET",
            "/analytics/overview",
            query={
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "tag": tag_query(tag),
            },
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
        """``GET /analytics/best-times`` - best times to post for a platform.
        The response has no ``data`` wrapper (see the sync client)."""
        return await self._client.request(
            "GET",
            "/analytics/best-times",
            query={"platform": platform, "timezone": timezone},
        )

    async def tags(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        platform: Optional[str] = None,
        min_posts: Optional[int] = None,
    ) -> Any:
        """``GET /analytics/tags`` - how each tag did against your normal
        (see the sync client)."""
        return await self._client.request(
            "GET",
            "/analytics/tags",
            query={
                "start_date": start_date,
                "end_date": end_date,
                "platform": platform,
                "min_posts": min_posts,
            },
        )
