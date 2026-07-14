"""Media resource: upload, list, check, rename/move, and delete library files."""

from __future__ import annotations

import os
from typing import IO, TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

from .._utils import NOT_GIVEN, NotGiven, drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Media", "AsyncMedia"]

FileInput = Union[bytes, bytearray, memoryview, str, "os.PathLike[str]", IO[bytes]]


def _coerce_file(file: FileInput, filename: Optional[str]) -> Tuple[str, bytes]:
    """Normalize the ``file`` argument to ``(filename, bytes)``.

    Accepts raw bytes, a file-like object opened in binary mode, or a path.
    The content is read fully into memory so automatic retries can resend it.
    """
    if isinstance(file, (str, os.PathLike)):
        path = os.fspath(file)
        with open(path, "rb") as handle:
            data = handle.read()
        return filename or os.path.basename(path), data
    if isinstance(file, (bytes, bytearray, memoryview)):
        return filename or "upload", bytes(file)
    if hasattr(file, "read"):
        data = file.read()
        if isinstance(data, str):
            raise TypeError(
                "file must be opened in binary mode ('rb'), got text data."
            )
        inferred = getattr(file, "name", None)
        if not filename and isinstance(inferred, str) and inferred:
            filename = os.path.basename(inferred)
        return filename or "upload", bytes(data)
    raise TypeError(
        "file must be bytes, a binary file-like object, or a file path; "
        f"got {type(file).__name__}."
    )


def _upload_form(
    *,
    name: Optional[str],
    folder: Optional[str],
    folder_id: Optional[str],
) -> Dict[str, Any]:
    return drop_none({"name": name, "folder": folder, "folder_id": folder_id})


class Media:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        search: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Any:
        """``GET /media`` - list library files."""
        return self._client.request(
            "GET",
            "/media",
            query={
                "limit": limit,
                "offset": offset,
                "search": search,
                "folder_id": folder_id,
            },
        )

    def get(self, media_id: str) -> Any:
        """``GET /media/{id}`` - fetch a single library file."""
        return self._client.request("GET", f"/media/{media_id}")

    def upload(
        self,
        *,
        file: FileInput,
        filename: Optional[str] = None,
        name: Optional[str] = None,
        folder: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Any:
        """``POST /media/upload`` - multipart upload (max 100MB inline).

        ``file`` is raw bytes, a binary file-like object, or a file path.
        A PDF is split into image slides and the response is a PdfUploadResult
        (``slides`` + ``media_ids``) instead of a single ``data`` item.
        For files over 100MB use ``upload_from_url`` (up to 1GB) or the
        ``create_upload_url`` presigned flow.
        """
        upload_name, content = _coerce_file(file, filename)
        return self._client.request(
            "POST",
            "/media/upload",
            files={"file": (upload_name, content)},
            data=_upload_form(name=name, folder=folder, folder_id=folder_id),
        )

    def upload_from_url(
        self,
        *,
        url: str,
        filename: Optional[str] = None,
        name: Optional[str] = None,
        folder: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Any:
        """``POST /media/upload-from-url`` - server-side fetch, up to 1GB.

        Files over 100MB are streamed in the background: the response has
        ``data.status == "processing"``; poll ``get()`` until ``"ready"``.
        """
        body = drop_none(
            {
                "url": url,
                "filename": filename,
                "name": name,
                "folder": folder,
                "folder_id": folder_id,
            }
        )
        return self._client.request("POST", "/media/upload-from-url", json=body)

    def upload_from_base64(
        self,
        *,
        data: str,
        mime_type: str,
        filename: Optional[str] = None,
        name: Optional[str] = None,
        folder: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Any:
        """``POST /media/upload-from-base64`` - upload base64-encoded data
        (without a data URI prefix)."""
        body = drop_none(
            {
                "data": data,
                "mime_type": mime_type,
                "filename": filename,
                "name": name,
                "folder": folder,
                "folder_id": folder_id,
            }
        )
        return self._client.request("POST", "/media/upload-from-base64", json=body)

    def create_upload_url(self) -> Any:
        """``POST /media/create-upload-url`` - mint a one-time presigned URL.

        Returns ``{"upload_url", "upload_token", "expires_in_seconds", ...}``.
        POST the file to ``upload_url`` as multipart form data (field name
        ``file``) with NO auth headers; the token in the URL authenticates the
        single upload and expires after 10 minutes.
        """
        return self._client.request("POST", "/media/create-upload-url")

    def check(
        self,
        *,
        url: Optional[str] = None,
        media_id: Optional[str] = None,
        size_bytes: Optional[int] = None,
        mime: Optional[str] = None,
    ) -> Any:
        """``POST /media/check`` - preflight platform compatibility.

        Provide one of: a public ``url``, an existing ``media_id``, or
        ``size_bytes`` + ``mime``.
        """
        body = drop_none(
            {
                "url": url,
                "media_id": media_id,
                "size_bytes": size_bytes,
                "mime": mime,
            }
        )
        return self._client.request("POST", "/media/check", json=body)

    def update(
        self,
        media_id: str,
        *,
        name: Optional[str] = None,
        folder_id: Union[str, None, NotGiven] = NOT_GIVEN,
    ) -> Any:
        """``PATCH /media/{id}`` - rename and/or move a file.

        Pass ``folder_id=None`` explicitly to move the file to the root
        ("All media"); omit it to leave the folder unchanged.
        """
        body: Dict[str, Any] = drop_none({"name": name})
        if not isinstance(folder_id, NotGiven):
            body["folder_id"] = folder_id
        return self._client.request("PATCH", f"/media/{media_id}", json=body)

    def delete(self, media_id: str) -> None:
        """``DELETE /media/{id}`` - delete a file. Returns ``None`` (204).

        Fails with 409 ``media_in_use`` if the file is attached to a
        scheduled or publishing post.
        """
        return self._client.request("DELETE", f"/media/{media_id}")


class AsyncMedia:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        search: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Any:
        """``GET /media`` - list library files."""
        return await self._client.request(
            "GET",
            "/media",
            query={
                "limit": limit,
                "offset": offset,
                "search": search,
                "folder_id": folder_id,
            },
        )

    async def get(self, media_id: str) -> Any:
        """``GET /media/{id}`` - fetch a single library file."""
        return await self._client.request("GET", f"/media/{media_id}")

    async def upload(
        self,
        *,
        file: FileInput,
        filename: Optional[str] = None,
        name: Optional[str] = None,
        folder: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Any:
        """``POST /media/upload`` - multipart upload (max 100MB inline)."""
        upload_name, content = _coerce_file(file, filename)
        return await self._client.request(
            "POST",
            "/media/upload",
            files={"file": (upload_name, content)},
            data=_upload_form(name=name, folder=folder, folder_id=folder_id),
        )

    async def upload_from_url(
        self,
        *,
        url: str,
        filename: Optional[str] = None,
        name: Optional[str] = None,
        folder: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Any:
        """``POST /media/upload-from-url`` - server-side fetch, up to 1GB."""
        body = drop_none(
            {
                "url": url,
                "filename": filename,
                "name": name,
                "folder": folder,
                "folder_id": folder_id,
            }
        )
        return await self._client.request("POST", "/media/upload-from-url", json=body)

    async def upload_from_base64(
        self,
        *,
        data: str,
        mime_type: str,
        filename: Optional[str] = None,
        name: Optional[str] = None,
        folder: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Any:
        """``POST /media/upload-from-base64`` - upload base64-encoded data."""
        body = drop_none(
            {
                "data": data,
                "mime_type": mime_type,
                "filename": filename,
                "name": name,
                "folder": folder,
                "folder_id": folder_id,
            }
        )
        return await self._client.request(
            "POST", "/media/upload-from-base64", json=body
        )

    async def create_upload_url(self) -> Any:
        """``POST /media/create-upload-url`` - mint a one-time presigned URL."""
        return await self._client.request("POST", "/media/create-upload-url")

    async def check(
        self,
        *,
        url: Optional[str] = None,
        media_id: Optional[str] = None,
        size_bytes: Optional[int] = None,
        mime: Optional[str] = None,
    ) -> Any:
        """``POST /media/check`` - preflight platform compatibility."""
        body = drop_none(
            {
                "url": url,
                "media_id": media_id,
                "size_bytes": size_bytes,
                "mime": mime,
            }
        )
        return await self._client.request("POST", "/media/check", json=body)

    async def update(
        self,
        media_id: str,
        *,
        name: Optional[str] = None,
        folder_id: Union[str, None, NotGiven] = NOT_GIVEN,
    ) -> Any:
        """``PATCH /media/{id}`` - rename and/or move a file.

        Pass ``folder_id=None`` explicitly to move the file to the root.
        """
        body: Dict[str, Any] = drop_none({"name": name})
        if not isinstance(folder_id, NotGiven):
            body["folder_id"] = folder_id
        return await self._client.request("PATCH", f"/media/{media_id}", json=body)

    async def delete(self, media_id: str) -> None:
        """``DELETE /media/{id}`` - delete a file. Returns ``None`` (204)."""
        return await self._client.request("DELETE", f"/media/{media_id}")
