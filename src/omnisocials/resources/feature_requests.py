"""Feature requests resource: requests to the OmniSocials team, for the
person who owns the key (their name and email are stored with it so the
team can answer). The person sees them in OmniSocials (Settings, Request a
feature) and gets an email when the status changes. No scope needed.

A request is ``{"id", "title", "summary", "status" (open, in_progress,
completed, declined), "team_answer", "team_replies": [{"message",
"created_at"}], "votes_count", "limit_id", "platform", "area", "source",
"created_at", "updated_at", "completed_at"}``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .._utils import drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["FeatureRequests", "AsyncFeatureRequests"]


def _create_body(
    summary: str,
    title: Optional[str],
    platform: Optional[str],
    area: Optional[str],
    limit_id: Optional[str],
) -> dict:
    return drop_none(
        {
            "summary": summary,
            "title": title,
            "platform": platform,
            "area": area,
            "limit_id": limit_id,
        }
    )


class FeatureRequests:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def create(
        self,
        *,
        summary: str,
        title: Optional[str] = None,
        platform: Optional[str] = None,
        area: Optional[str] = None,
        limit_id: Optional[str] = None,
    ) -> Any:
        """``POST /feature-requests`` - send a request. Send it only when the
        person asked for it.

        ``summary`` (10 to 1000 characters) says what the person wants to do
        and why; ``title`` (at most 120) is made from it when left out.
        ``limit_id`` is the ``id`` of the ``limits.list()`` entry the request
        is about. Returns ``{"outcome", "data"}``: ``outcome`` is
        ``"created"`` (a new request), ``"voted"`` (a vote added to the
        organisation's open request for the same gap) or
        ``"already_requested"`` (this person already has an open request for
        it; ``data`` is that request).

        Errors: ``400 invalid_summary`` / ``invalid_title`` /
        ``invalid_platform`` / ``invalid_area`` / ``unknown_limit``;
        ``409 not_requestable`` (a platform rule or a choice of OmniSocials:
        the entry is in ``error.body["error"]["limit"]``, nothing was
        stored); ``429 too_many_requests`` (10 an hour per person).
        """
        return self._client.request(
            "POST",
            "/feature-requests",
            json=_create_body(summary, title, platform, area, limit_id),
        )

    def list(self) -> Any:
        """``GET /feature-requests`` - the person's own requests, newest
        first, at most 50: ``{"data": [FeatureRequest]}``."""
        return self._client.request("GET", "/feature-requests")

    def get(self, request_id: Union[str, int]) -> Any:
        """``GET /feature-requests/{id}`` - one request with its status and
        the team's replies. Errors: ``400 invalid_id``, ``404 not_found``."""
        return self._client.request("GET", f"/feature-requests/{request_id}")


class AsyncFeatureRequests:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def create(
        self,
        *,
        summary: str,
        title: Optional[str] = None,
        platform: Optional[str] = None,
        area: Optional[str] = None,
        limit_id: Optional[str] = None,
    ) -> Any:
        """``POST /feature-requests`` - send a request (see
        :meth:`FeatureRequests.create`)."""
        return await self._client.request(
            "POST",
            "/feature-requests",
            json=_create_body(summary, title, platform, area, limit_id),
        )

    async def list(self) -> Any:
        """``GET /feature-requests`` - the person's own requests."""
        return await self._client.request("GET", "/feature-requests")

    async def get(self, request_id: Union[str, int]) -> Any:
        """``GET /feature-requests/{id}`` - one request."""
        return await self._client.request("GET", f"/feature-requests/{request_id}")
