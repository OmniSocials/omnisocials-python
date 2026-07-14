"""Folders resource: organize media library files into folders."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .._utils import NOT_GIVEN, NotGiven, drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Folders", "AsyncFolders"]


class Folders:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(self) -> Any:
        """``GET /folders`` - list media folders (with per-folder file counts)."""
        return self._client.request("GET", "/folders")

    def create(self, *, name: str, parent_id: Optional[str] = None) -> Any:
        """``POST /folders`` - create a folder (optionally nested under
        ``parent_id``)."""
        body = drop_none({"name": name, "parent_id": parent_id})
        return self._client.request("POST", "/folders", json=body)

    def update(
        self,
        folder_id: str,
        *,
        name: Optional[str] = None,
        parent_id: Union[str, None, NotGiven] = NOT_GIVEN,
    ) -> Any:
        """``PATCH /folders/{id}`` - rename and/or move a folder.

        Pass ``parent_id=None`` explicitly to move the folder to the top
        level; omit it to leave the parent unchanged.
        """
        body: Dict[str, Any] = drop_none({"name": name})
        if not isinstance(parent_id, NotGiven):
            body["parent_id"] = parent_id
        return self._client.request("PATCH", f"/folders/{folder_id}", json=body)

    def delete(self, folder_id: str) -> None:
        """``DELETE /folders/{id}`` - delete a folder. Returns ``None`` (204).

        The folder's media is NOT deleted: files move to the root and
        subfolders move up to the deleted folder's parent.
        """
        return self._client.request("DELETE", f"/folders/{folder_id}")


class AsyncFolders:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(self) -> Any:
        """``GET /folders`` - list media folders (with per-folder file counts)."""
        return await self._client.request("GET", "/folders")

    async def create(self, *, name: str, parent_id: Optional[str] = None) -> Any:
        """``POST /folders`` - create a folder (optionally nested under
        ``parent_id``)."""
        body = drop_none({"name": name, "parent_id": parent_id})
        return await self._client.request("POST", "/folders", json=body)

    async def update(
        self,
        folder_id: str,
        *,
        name: Optional[str] = None,
        parent_id: Union[str, None, NotGiven] = NOT_GIVEN,
    ) -> Any:
        """``PATCH /folders/{id}`` - rename and/or move a folder.

        Pass ``parent_id=None`` explicitly to move the folder to the top level.
        """
        body: Dict[str, Any] = drop_none({"name": name})
        if not isinstance(parent_id, NotGiven):
            body["parent_id"] = parent_id
        return await self._client.request("PATCH", f"/folders/{folder_id}", json=body)

    async def delete(self, folder_id: str) -> None:
        """``DELETE /folders/{id}`` - delete a folder. Returns ``None`` (204)."""
        return await self._client.request("DELETE", f"/folders/{folder_id}")
