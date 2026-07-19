"""Inbox resource: social inbox conversations, messages, and replies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import quote

from .._utils import drop_none

if TYPE_CHECKING:
    from .._client import AsyncOmniSocials, OmniSocials

__all__ = ["Inbox", "AsyncInbox"]


def _encode_id(conversation_id: str) -> str:
    """Percent-encode a conversation id for use as a single path segment.

    LinkedIn conversation ids contain reserved characters such as ``:`` and
    ``()`` (e.g. ``linkedin_comment_urn:li:activity:123``), so every reserved
    character must be encoded; ``safe=""`` leaves nothing unescaped.
    """
    return quote(conversation_id, safe="")


def _reply_body(
    *,
    text: str,
    attachment_url: Optional[str],
    attachment_type: Optional[str],
) -> Dict[str, Any]:
    return drop_none(
        {
            "text": text,
            "attachment_url": attachment_url,
            "attachment_type": attachment_type,
        }
    )


class Inbox:
    def __init__(self, client: "OmniSocials") -> None:
        self._client = client

    def list_conversations(
        self,
        *,
        platform: Optional[str] = None,
        type: Optional[str] = None,
        unread: Optional[bool] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations`` - list social inbox conversations (DMs,
        comments, mentions) across connected platforms, newest activity first.

        Filter by ``platform`` (``"instagram"``, ``"facebook"``,
        ``"linkedin"``), ``type`` (``"dm"``, ``"comment"``, ``"mention"``),
        and ``unread``. ``limit`` is 1-100. Uses cursor pagination: pass the
        previous response's ``pagination.next_cursor`` as ``cursor`` to keep
        paging while ``pagination.has_more`` is true.
        """
        return self._client.request(
            "GET",
            "/inbox/conversations",
            query={
                "platform": platform,
                "type": type,
                "unread": unread,
                "limit": limit,
                "cursor": cursor,
            },
        )

    def get_messages(
        self,
        conversation_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations/{id}/messages`` - full message thread for
        one conversation, newest first.

        Uses cursor pagination (``limit`` / ``cursor``). The id is URL-encoded
        for you, so pass it exactly as returned (LinkedIn ids contain ``:`` and
        ``()``).
        """
        return self._client.request(
            "GET",
            f"/inbox/conversations/{_encode_id(conversation_id)}/messages",
            query={"limit": limit, "cursor": cursor},
        )

    def mark_read(self, conversation_id: str) -> Any:
        """``POST /inbox/conversations/{id}/read`` - mark every message in the
        conversation as read.

        Returns ``{"conversation_id", "marked_read"}`` where ``marked_read`` is
        the count of messages that were newly marked read.
        """
        return self._client.request(
            "POST", f"/inbox/conversations/{_encode_id(conversation_id)}/read"
        )

    def reply(
        self,
        conversation_id: str,
        text: str,
        *,
        attachment_url: Optional[str] = None,
        attachment_type: Optional[str] = None,
    ) -> Any:
        """``POST /inbox/conversations/{id}/reply`` - send a reply into the
        conversation (a DM message, or a reply to the comment/mention).

        Optionally attach a single media asset by public URL with
        ``attachment_url`` + ``attachment_type`` (``"image"``, ``"video"``,
        ``"audio"``, or ``"file"``). Returns the created outbound message.
        """
        body = _reply_body(
            text=text,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
        )
        return self._client.request(
            "POST",
            f"/inbox/conversations/{_encode_id(conversation_id)}/reply",
            json=body,
        )


class AsyncInbox:
    def __init__(self, client: "AsyncOmniSocials") -> None:
        self._client = client

    async def list_conversations(
        self,
        *,
        platform: Optional[str] = None,
        type: Optional[str] = None,
        unread: Optional[bool] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations`` - list social inbox conversations (DMs,
        comments, mentions) across connected platforms, newest activity first.

        Filter by ``platform`` (``"instagram"``, ``"facebook"``,
        ``"linkedin"``), ``type`` (``"dm"``, ``"comment"``, ``"mention"``),
        and ``unread``. ``limit`` is 1-100. Uses cursor pagination: pass the
        previous response's ``pagination.next_cursor`` as ``cursor`` to keep
        paging while ``pagination.has_more`` is true.
        """
        return await self._client.request(
            "GET",
            "/inbox/conversations",
            query={
                "platform": platform,
                "type": type,
                "unread": unread,
                "limit": limit,
                "cursor": cursor,
            },
        )

    async def get_messages(
        self,
        conversation_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """``GET /inbox/conversations/{id}/messages`` - full message thread for
        one conversation, newest first.

        Uses cursor pagination (``limit`` / ``cursor``). The id is URL-encoded
        for you, so pass it exactly as returned (LinkedIn ids contain ``:`` and
        ``()``).
        """
        return await self._client.request(
            "GET",
            f"/inbox/conversations/{_encode_id(conversation_id)}/messages",
            query={"limit": limit, "cursor": cursor},
        )

    async def mark_read(self, conversation_id: str) -> Any:
        """``POST /inbox/conversations/{id}/read`` - mark every message in the
        conversation as read.

        Returns ``{"conversation_id", "marked_read"}`` where ``marked_read`` is
        the count of messages that were newly marked read.
        """
        return await self._client.request(
            "POST", f"/inbox/conversations/{_encode_id(conversation_id)}/read"
        )

    async def reply(
        self,
        conversation_id: str,
        text: str,
        *,
        attachment_url: Optional[str] = None,
        attachment_type: Optional[str] = None,
    ) -> Any:
        """``POST /inbox/conversations/{id}/reply`` - send a reply into the
        conversation (a DM message, or a reply to the comment/mention).

        Optionally attach a single media asset by public URL with
        ``attachment_url`` + ``attachment_type`` (``"image"``, ``"video"``,
        ``"audio"``, or ``"file"``). Returns the created outbound message.
        """
        body = _reply_body(
            text=text,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
        )
        return await self._client.request(
            "POST",
            f"/inbox/conversations/{_encode_id(conversation_id)}/reply",
            json=body,
        )
