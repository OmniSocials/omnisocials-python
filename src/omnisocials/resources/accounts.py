"""Accounts resource: connected social accounts for the API key's workspace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Optional

from .._utils import path_segment

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Accounts", "AsyncAccounts"]


class Accounts:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /accounts`` - list connected social accounts.

        The response also carries ``workspace_id`` and ``workspace_name`` for
        the workspace the API key belongs to.
        """
        return self._client.request("GET", "/accounts")

    def get(self, account_id: str) -> Any:
        """``GET /accounts/{id}`` - fetch a single connected account.

        An X account also carries ``x_statistics``: ``posts``, ``followers``,
        ``post_schedule``, ``source``, ``billing``, ``state`` and
        ``paused_reason`` (``None`` when it could not be read)."""
        return self._client.request("GET", f"/accounts/{path_segment(account_id)}")

    def update(
        self, account_id: str, *, x_statistics: Optional[Mapping[str, Any]]
    ) -> Any:
        """``PATCH /accounts/{id}`` - change how often the X statistics of an
        X account are read.

        ``x_statistics`` is ``{"posts": ..., "followers": ..., "post_schedule": ...}``
        with one key or more; only the keys you give are sent. ``posts`` is
        ``full`` (5 checks), ``light`` (2 checks) or ``off``; ``followers`` is
        ``daily``, ``weekly`` or ``off``. X bills every read and OmniSocials
        passes X's price on as credits (half a credit per post check, plus
        half for a video or GIF, 1 credit per follower count). Needs the
        opt-in scope ``accounts:write`` and billing rights (manage_billing)
        for the key's creator. OmniSocials Connect keys (the partner's own X
        app pays) also take ``posts="custom"`` with ``post_schedule``
        (``{"at": ["1h", "1d"], "then_every": "7d", "until": "90d"}``),
        ``followers`` ``hourly`` / ``6h``, and ``x_statistics=None``, which is
        sent as ``null``: follow the customer's setting again.

        Returns ``{"data": account}`` with the new ``x_statistics``. Errors:
        ``400 validation_error`` / ``schedule_invalid`` / ``not_supported``
        (not an X account), ``403 forbidden``, ``404 not_found``.
        """
        return self._client.request(
            "PATCH",
            f"/accounts/{path_segment(account_id)}",
            json=_update_body(x_statistics),
        )


class AsyncAccounts:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /accounts`` - list connected social accounts."""
        return await self._client.request("GET", "/accounts")

    async def get(self, account_id: str) -> Any:
        """``GET /accounts/{id}`` - fetch a single connected account."""
        return await self._client.request("GET", f"/accounts/{path_segment(account_id)}")

    async def update(
        self, account_id: str, *, x_statistics: Optional[Mapping[str, Any]]
    ) -> Any:
        """``PATCH /accounts/{id}`` - change how often the X statistics of an
        X account are read (see :meth:`Accounts.update`)."""
        return await self._client.request(
            "PATCH",
            f"/accounts/{path_segment(account_id)}",
            json=_update_body(x_statistics),
        )


def _update_body(x_statistics: Optional[Mapping[str, Any]]) -> dict:
    # None is sent as null (Connect: follow the customer); a mapping is sent
    # with exactly the keys the caller gave.
    return {"x_statistics": None if x_statistics is None else dict(x_statistics)}
