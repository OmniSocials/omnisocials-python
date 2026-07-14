"""Accounts resource: connected social accounts for the API key's workspace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
        """``GET /accounts/{id}`` - fetch a single connected account."""
        return self._client.request("GET", f"/accounts/{account_id}")


class AsyncAccounts:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /accounts`` - list connected social accounts."""
        return await self._client.request("GET", "/accounts")

    async def get(self, account_id: str) -> Any:
        """``GET /accounts/{id}`` - fetch a single connected account."""
        return await self._client.request("GET", f"/accounts/{account_id}")
